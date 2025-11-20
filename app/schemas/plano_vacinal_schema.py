from marshmallow import Schema, fields, validate, ValidationError

def _raise_error():
    raise ValidationError("O campo 'dose' deve ser um número inteiro positivo (>= 1) ou a string 'Única'.")

class PacienteSchema(Schema):
    """Schema para validar os dados do paciente."""
    data_nascimento = fields.Date(
        required=True,
        error_messages={"required": "A data de nascimento é obrigatória.", "invalid": "Formato de data inválido. Use AAAA-MM-DD."}
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
        error_messages={"required": "A data de aplicação é obrigatória.", "invalid": "Formato de data inválido. Use AAAA-MM-DD."}
    )
    dose = fields.Field(
        required=True,
        validate=[
            lambda d: (
                isinstance(d, int) and d >= 1
            ) or (
                isinstance(d, str) and d.lower() == "única"
            ) or (
                _raise_error()
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
    # 'many=True' indica que este campo é uma lista de objetos.
    # 'required=False' permite que a API seja chamada para um recém-nascido sem vacinas.
    carteira_vacinacao = fields.Nested(
        DoseAplicadaSchema,
        many=True,
        required=False
    )