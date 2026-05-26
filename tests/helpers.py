import datetime
from dateutil.relativedelta import relativedelta
from unittest.mock import patch
from app.services.plano_vacinal_service import PlanoVacinalService


def today():
    return datetime.date.today()


def birth_date_ago(years=0, months=0, days=0):
    """Return a date that is the given years/months/days before today."""
    return today() - relativedelta(years=years, months=months, days=days)


def dose(vaccine_code, date, dose_num=1):
    """Build a dose-history entry dict for test input."""
    return {'vacina_codigo': vaccine_code, 'data_aplicacao': date, 'dose': dose_num}


def run_engine(date_of_birth, doses=None):
    """Run the inference engine in isolation (no HTTP, no database)."""
    if doses is None:
        doses = []
    patient = {'data_nascimento': date_of_birth, 'sexo': 'M'}
    with patch('app.services.plano_vacinal_service.log_repository'):
        svc = PlanoVacinalService()
        svc._paciente_dados = patient
        svc._carteira_dados = doses
        engine = svc._build_engine()
        setattr(engine, 'paciente_dados', patient)
        setattr(engine, 'carteira_dados', doses)
        engine.reset()
        engine.run()
        return svc._collect_results(engine)


def get_recommended(result):
    """Extract the set of recommended vaccine names from an engine result."""
    return {v['vacina'] for v in result['vacinas_recomendadas']}


def get_scheduled(result):
    """Extract the set of scheduled (future) vaccine names from an engine result."""
    return {v['vacina'] for v in result['vacinas_aprazadas']}


def get_contraindicated(result):
    """Extract the set of contraindicated vaccine names from an engine result."""
    return {v['vacina'] for v in result['vacinas_contraindicadas']}


def get_up_to_date(result):
    """Extract the set of up-to-date vaccine names from an engine result."""
    return {v['vacina'] for v in result['vacinas_em_dia']}


def get_scheduled_for(result, vaccine):
    """Return the scheduling entry for a specific vaccine, or None if not found."""
    return next((v for v in result['vacinas_aprazadas'] if v['vacina'] == vaccine), None)
