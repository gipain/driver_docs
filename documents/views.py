import io
import os
import subprocess
import tempfile
import zipfile
from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import DetailView, ListView

from core.models import Company
from core.vat import calculate_vat
from partners.models import Contract
from trips.models import Trip

from .autofill import build_act_context
from .fill_ttn import fill_ttn
from .models import TTN, Act, ActLine, CargoLine
from .numbering import next_act_number, next_ttn_number
from .registry import build_monthly_registry_workbook
from .summary import build_summary_workbook

#спільні функції генерації документів 


def _generate_ttn_for_trip(trip) -> TTN:
    """Створює TTN + один рядок CargoLine для підтвердженого рейсу, що ще
    не має ТТН. Кидає ValueError, якщо рейс не готовий."""
    if trip.status != Trip.Status.CONFIRMED:
        raise ValueError('рейс не підтверджено')
    if hasattr(trip, 'ttn'):
        return trip.ttn

    vat_amount, amount_with_vat = calculate_vat(trip.amount_no_vat)
    number = next_ttn_number()
    ttn = TTN.objects.create(
        trip=trip, number=number, date=trip.date,
        place=trip.carrier.address, accompanying_docs=f'Видат. накл. {number}',
    )
    CargoLine.objects.create(
        ttn=ttn, name=trip.cargo_name or 'Вантаж', unit=trip.cargo_unit,
        qty=trip.places_count, unit_price=0, amount=amount_with_vat,
        packaging=trip.cargo_packaging, weight_t=trip.weight_t,
    )
    return ttn


def _generate_act_for_contract(contract, trips) -> Act:
    """Створює Act + ActLine для переданих (ще не включених у жоден акт)
    підтверджених рейсів одного договору."""
    trips = list(trips)
    if not trips:
        raise ValueError('немає підтверджених рейсів без акту за цим договором')
    executor = Company.objects.first()
    if executor is None:
        raise ValueError('не заповнено профіль власної компанії (Company)')

    amount_no_vat = sum((tr.amount_no_vat for tr in trips), trips[0].amount_no_vat * 0)
    vat_amount, amount_with_vat = calculate_vat(amount_no_vat)
    act = Act.objects.create(
        number=next_act_number(),
        date=max(tr.date for tr in trips),
        contract=contract, customer=contract.counterparty, executor=executor,
        amount_no_vat=amount_no_vat, vat_amount=vat_amount, amount_with_vat=amount_with_vat,
    )
    for trip in trips:
        ActLine.objects.create(
            act=act, trip=trip,
            description=f'{trip.loading_address} - {trip.unloading_address}',
            weight_t=trip.weight_t, amount=trip.amount_no_vat,
        )
    return act


def _fill_ttn_bytes(ttn) -> bytes:
    wb = fill_ttn(ttn)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _ttn_pdf_bytes(ttn) -> bytes | None:
    """None, якщо LibreOffice на машині не знайдено - виклик має сам
    вирішити, чи це фатально (запасний варіант дня 1: лишити xlsx)."""
    if not Path(settings.SOFFICE_PATH).exists():
        return None
    with tempfile.TemporaryDirectory() as tmp_dir:
        xlsx_path = Path(tmp_dir) / f'TTN_{ttn.number}.xlsx'
        xlsx_path.write_bytes(_fill_ttn_bytes(ttn))
        subprocess.run(
            [settings.SOFFICE_PATH, '--headless', '--convert-to', 'pdf',
             '--outdir', tmp_dir, str(xlsx_path)],
            check=True, timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        )
        pdf_path = xlsx_path.with_suffix('.pdf')
        return pdf_path.read_bytes() if pdf_path.exists() else None


def _font_uri(filename: str) -> str:
    return (Path(settings.BASE_DIR) / 'static' / 'fonts' / filename).resolve().as_uri()


def _render_act_html(act) -> str:
    ctx = build_act_context(act)
    return render_to_string('documents/act_pdf.html', {
        'act': act,
        'ctx': ctx,
        'font_regular_uri': _font_uri('DejaVuSans.ttf'),
        'font_bold_uri': _font_uri('DejaVuSans-Bold.ttf'),
    })


def _act_pdf_bytes(act) -> bytes:
    if settings.GTK_RUNTIME_PATH:
        os.add_dll_directory(settings.GTK_RUNTIME_PATH)
    from weasyprint import HTML  # локальний імпорт - після add_dll_directory

    return HTML(string=_render_act_html(act), base_url='http://localhost/').write_pdf()


# ---------- окремі документи ----------


class GenerateActView(View):
    """Формує акт здачі-прийняття робіт за договором (день 9)."""

    def post(self, request, contract_pk):
        contract = get_object_or_404(Contract, pk=contract_pk)
        trips = Trip.objects.filter(
            contract=contract, status=Trip.Status.CONFIRMED, act_lines__isnull=True,
        )
        try:
            act = _generate_act_for_contract(contract, trips)
        except ValueError as exc:
            messages.error(request, str(exc).capitalize() + '.')
            return redirect('partners:contract_list')
        messages.success(request, f'Акт №{act.number} сформовано на основі {trips.count()} рейс(ів).')
        return redirect('documents:act_detail', pk=act.pk)


class GenerateTTNView(View):
    """Формує ТТН для конкретного підтвердженого рейсу (день 10)."""

    def post(self, request, trip_pk):
        trip = get_object_or_404(Trip, pk=trip_pk)
        if hasattr(trip, 'ttn'):
            messages.error(request, f'Рейс №{trip.pk} уже має ТТН №{trip.ttn.number}.')
            return redirect('trips:trip_detail', pk=trip_pk)
        try:
            ttn = _generate_ttn_for_trip(trip)
        except ValueError as exc:
            messages.error(request, str(exc).capitalize() + '.')
            return redirect('trips:trip_detail', pk=trip_pk)
        messages.success(request, f'ТТН №{ttn.number} сформовано для рейсу №{trip.pk}.')
        return redirect('trips:trip_detail', pk=trip_pk)


class TTNXlsxView(View):
    """Кнопка «Завантажити ТТН (xlsx)» - завжди доступна, без зовнішніх
    залежностей (день 10)."""

    def get(self, request, pk):
        ttn = get_object_or_404(TTN, pk=pk)
        response = HttpResponse(
            _fill_ttn_bytes(ttn),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="TTN_{ttn.number}.xlsx"'
        return response


class TTNPdfView(View):
    """Кнопка «Завантажити ТТН (pdf)» - конвертує заповнену заготовку
    через LibreOffice headless (день 10). Якщо soffice.exe на машині не
    знайдено - офіційно допустимий запасний варіант із дня 1."""

    def get(self, request, pk):
        ttn = get_object_or_404(TTN, pk=pk)
        pdf_bytes = _ttn_pdf_bytes(ttn)
        if pdf_bytes is None:
            messages.error(
                request,
                'LibreOffice не знайдено на цій машині - PDF для ТТН недоступний, '
                'скористайтесь варіантом xlsx.',
            )
            return redirect('trips:trip_detail', pk=ttn.trip_id)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="TTN_{ttn.number}.pdf"'
        return response


class ActListView(ListView):
    model = Act
    template_name = 'documents/act_list.html'
    context_object_name = 'acts'
    queryset = Act.objects.select_related('customer', 'executor', 'contract')


class ActDetailView(DetailView):
    model = Act
    template_name = 'documents/act_detail.html'
    context_object_name = 'act'


class ActPreviewView(View):
    """Показує той самий HTML, що піде у PDF, - зручно перевірити
    верстку в браузері (день 9)."""

    def get(self, request, pk):
        act = get_object_or_404(Act, pk=pk)
        return HttpResponse(_render_act_html(act))


class ActPdfView(View):
    """Кнопка «Завантажити PDF» (день 9)."""

    def get(self, request, pk):
        act = get_object_or_404(Act, pk=pk)
        pdf_bytes = _act_pdf_bytes(act)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Act_{act.number}.pdf"'
        return response


# ---------- реєстр, зведений звіт і пакетна генерація ----------


def _period_from_get(request):
    return parse_date(request.GET.get('start') or ''), parse_date(request.GET.get('end') or '')


def _period_from_post(request):
    return parse_date(request.POST.get('start') or ''), parse_date(request.POST.get('end') or '')


def registry_page(request):
    today = date.today()
    start = request.GET.get('start') or today.replace(day=1).isoformat()
    end = request.GET.get('end') or today.isoformat()
    return render(request, 'documents/registry.html', {'start': start, 'end': end})


class RegistryXlsxView(View):
    def get(self, request):
        start, end = _period_from_get(request)
        if not (start and end):
            return HttpResponseBadRequest('Вкажіть коректний період (start, end).')
        wb = build_monthly_registry_workbook(start, end)
        buf = io.BytesIO()
        wb.save(buf)
        response = HttpResponse(
            buf.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="registry_{start}_{end}.xlsx"'
        return response


class SummaryXlsxView(View):
    def get(self, request):
        start, end = _period_from_get(request)
        if not (start and end):
            return HttpResponseBadRequest('Вкажіть коректний період (start, end).')
        group_by = request.GET.get('group_by', 'counterparty')
        wb = build_summary_workbook(start, end, group_by)
        buf = io.BytesIO()
        wb.save(buf)
        response = HttpResponse(
            buf.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="summary_{group_by}_{start}_{end}.xlsx"'
        return response


class BatchGenerateView(View):
    """Пакетна генерація за період (день 11): для кожного підтвердженого
    рейсу без ТТН - формує ТТН (xlsx (+pdf, якщо є LibreOffice)); для
    кожного договору з рейсами без акту - формує акт (pdf); додає реєстр
    і зведений звіт; усе разом пакує в ZIP. Помилка на одному рейсі не
    зупиняє решту пакета - лише потрапляє в errors.txt всередині архіву."""

    def post(self, request):
        start, end = _period_from_post(request)
        if not (start and end):
            messages.error(request, 'Вкажіть коректний період для пакетної генерації.')
            return redirect('documents:registry')

        trips = list(Trip.objects.filter(date__range=(start, end), status=Trip.Status.CONFIRMED))
        errors = []
        files = []
        contract_trips = {}

        for trip in trips:
            try:
                ttn = _generate_ttn_for_trip(trip)
                files.append((f'TTN/TTN_{ttn.number}.xlsx', _fill_ttn_bytes(ttn)))
                pdf_bytes = _ttn_pdf_bytes(ttn)
                if pdf_bytes:
                    files.append((f'TTN/TTN_{ttn.number}.pdf', pdf_bytes))
            except Exception as exc:
                errors.append(f'Рейс №{trip.pk} (ТТН): {exc}')
            contract_trips.setdefault(trip.contract_id, []).append(trip)

        for contract_id, cts in contract_trips.items():
            pending = [t for t in cts if not t.act_lines.exists()]
            if not pending:
                continue
            try:
                act = _generate_act_for_contract(pending[0].contract, pending)
                files.append((f'Acts/Act_{act.number}.pdf', _act_pdf_bytes(act)))
            except Exception as exc:
                errors.append(f'Договір №{contract_id} (акт): {exc}')

        registry_buf = io.BytesIO()
        build_monthly_registry_workbook(start, end).save(registry_buf)
        files.append((f'registry_{start}_{end}.xlsx', registry_buf.getvalue()))

        summary_buf = io.BytesIO()
        build_summary_workbook(start, end, 'counterparty').save(summary_buf)
        files.append((f'summary_{start}_{end}.xlsx', summary_buf.getvalue()))

        # Django messages тут не спрацюють - у відповідь одразу йде файл,
        # а не сторінка, на якій вони могли б показатись. Тому підсумок
        # пишемо прямо у файл всередині архіву - він і лишається доказом
        # результату пакетної генерації.
        manifest = [
            f'Період: {start} - {end}',
            f'Підтверджених рейсів у періоді: {len(trips)}',
            f'Помилок: {len(errors)}',
        ]
        files.append(('manifest.txt', ('\n'.join(manifest)).encode('utf-8')))
        if errors:
            files.append(('errors.txt', ('\n'.join(errors)).encode('utf-8')))

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for name, content in files:
                zf.writestr(name, content)

        response = HttpResponse(zip_buf.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="batch_{start}_{end}.zip"'
        return response
