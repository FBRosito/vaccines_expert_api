from datetime import date
from marshmallow import Schema, fields, validate, ValidationError

# --- FUNÇÕES DE VALIDAÇÃO CUSTOMIZADAS ---

def validate_not_future(value):
    """Valida se a data fornecida não é futura."""
    if value > date.today():
        raise ValidationError("A data não pode ser no futuro.")

def validate_reasonable_age(value):
    """
    Valida se a data de nascimento não resulta em uma idade irreal (> 130 anos).
    """
    today = date.today()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    
    if age > 130:
        raise ValidationError(f"Data inválida. A idade calculada ({age} anos) excede o limite máximo permitido.")

def _raise_error_dose():
    raise ValidationError("O campo 'dose' deve ser um número inteiro positivo (>= 1) ou a string 'Única'.")

# --- SCHEMAS ---

class PacienteSchema(Schema):
    """Schema para validar os dados do paciente."""
    data_nascimento = fields.Date(
        required=True,
        error_messages={
            "required": "A data de nascimento é obrigatória.", 
            "invalid": "Formato de data inválido. Use AAAA-MM-DD."
        },
        validate=[validate_not_future, validate_reasonable_age]
    )
    sexo = fields.Str(
        required=True,
        validate=validate.OneOf(["Masculino", "Feminino", "Outro"]),
        error_messages={"required": "O sexo é obrigatório."}
    )

class DoseAplicadaSchema(Schema):
    """Schema para validar cada dose de vacina na carteira."""
    vacina_codigo = fields.Str(
        required=True,
        error_messages={"required": "O código da vacina é obrigatório."}
    )
    data_aplicacao = fields.Date(
        required=True,
        error_messages={
            "required": "A data de aplicação é obrigatória.", 
            "invalid": "Formato de data inválido. Use AAAA-MM-DD."
        },
        validate=[validate_not_future]
    )
    dose = fields.Field(
        required=True,
        validate=[
            lambda d: (
                isinstance(d, int) and d >= 1
            ) or (
                isinstance(d, str) and d.lower() in ["única", "unica", "ref", "reforço", "reforco", "1º reforço", "2º reforço", "ref 1", "ref 2", "ref 10 anos"]
            ) or (
                _raise_error_dose()
            )
        ],
        error_messages={
            "required": "O número/descrição da dose é obrigatório.",
        }
    )

class PlanoVacinalInputSchema(Schema):
    """Schema principal para validar a entrada do simulador de plano vacinal."""
    paciente = fields.Nested(
        PacienteSchema,
        required=True,
        error_messages={"required": "Os dados do paciente são obrigatórios."}
    )
    carteira_vacinacao = fields.Nested(
        DoseAplicadaSchema,
        many=True,
        required=False
    )