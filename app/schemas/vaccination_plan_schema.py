from datetime import date
from marshmallow import Schema, fields, validate, ValidationError, pre_load

# --- Validation helpers ---

def validate_not_future(value):
    """Reject dates that are in the future."""
    if value > date.today():
        raise ValidationError("A data não pode ser no futuro.")

def validate_reasonable_age(value):
    """Reject birth dates implying age > 130 years."""
    today = date.today()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if age > 130:
        raise ValidationError(f"Data de nascimento inválida. Idade ({age} anos) excede o limite.")

# --- FHIR sub-schemas ---

class CodingSchema(Schema):
    """Maps to vaccineCode.coding[] — vaccine code (CVX, SNOMED, or SIPNI proprietary)."""
    system = fields.Str()
    code = fields.Str(required=True)
    display = fields.Str()

class VaccineCodeSchema(Schema):
    """Maps to resource.vaccineCode."""
    coding = fields.List(fields.Nested(CodingSchema), required=True)

class ProtocolAppliedSchema(Schema):
    """Maps to resource.protocolApplied[] — holds the dose number in FHIR."""
    doseNumberPositiveInt = fields.Int()
    doseNumberString = fields.Str()

class FHIRPatientResourceSchema(Schema):
    """FHIR Patient resource schema."""
    resourceType = fields.Str(validate=validate.Equal("Patient"), required=True)
    birthDate = fields.Date(
        required=True,
        validate=[validate_not_future, validate_reasonable_age],
        error_messages={"invalid": "Formato de data inválido. Use YYYY-MM-DD."}
    )
    gender = fields.Str(
        required=True,
        validate=validate.OneOf(["male", "female", "other", "unknown"]),
        error_messages={"validator_failed": "Gênero deve ser 'male', 'female', 'other' ou 'unknown'."}
    )

class FHIRImmunizationResourceSchema(Schema):
    """FHIR Immunization resource schema."""
    resourceType = fields.Str(validate=validate.Equal("Immunization"), required=True)
    status = fields.Str(validate=validate.Equal("completed"), missing="completed")
    vaccineCode = fields.Nested(VaccineCodeSchema, required=True)
    occurrenceDateTime = fields.Date(
        required=True,
        validate=[validate_not_future],
        attribute="occurrenceDateTime"
    )
    protocolApplied = fields.List(fields.Nested(ProtocolAppliedSchema), required=True)

class EntryResourceSchema(Schema):
    """A single Bundle.entry item — may contain a Patient or an Immunization resource."""
    resource = fields.Dict(required=True)

    @pre_load
    def validate_resource_type(self, data, **kwargs):
        resource = data.get('resource', {})
        res_type = resource.get('resourceType')

        if res_type == 'Patient':
            schema = FHIRPatientResourceSchema()
            errors = schema.validate(resource)
            if errors: raise ValidationError(errors, field_name="resource (Patient)")
        elif res_type == 'Immunization':
            schema = FHIRImmunizationResourceSchema()
            errors = schema.validate(resource)
            if errors: raise ValidationError(errors, field_name="resource (Immunization)")
        return data

class FHIRBundleSchema(Schema):
    """Top-level FHIR Bundle schema — the expected request body for the vaccination plan endpoint."""
    resourceType = fields.Str(validate=validate.Equal("Bundle"), required=True)
    type = fields.Str(validate=validate.OneOf(["collection", "transaction", "document"]), missing="collection")
    entry = fields.List(fields.Nested(EntryResourceSchema), required=True)
