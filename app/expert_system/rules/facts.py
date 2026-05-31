import datetime
from schema import Or
from experta import Fact, Field


class Patient(Fact):
    """Input fact representing the patient."""
    birth_date = Field(datetime.date, mandatory=True)

class Age(Fact):
    """
    Input fact with the patient's computed age.
    Includes birth_date so future-scheduling rules can anchor dates to birth date.
    Note: `months` stores total months (years * 12 + remaining months), not remainder alone.
    """
    years = Field(int, mandatory=True)
    months = Field(int, mandatory=True)
    days = Field(int, mandatory=True)
    birth_date = Field(datetime.date, mandatory=True)

class AppliedDose(Fact):
    """Input fact representing a previously administered vaccine dose."""
    vaccine_code = Field(str, mandatory=True)
    date_applied = Field(datetime.date, mandatory=True)
    dose = Field(Or(str, int), mandatory=True)

class ImmediateRecommendation(Fact):
    """Output fact: the patient should receive this vaccine today."""
    vaccine = Field(str, mandatory=True)
    dose = Field(Or(str, int), mandatory=True)
    explanation = Field(str, mandatory=True)

class FutureSchedule(Fact):
    """Output fact: the patient should schedule this vaccine for a future date."""
    vaccine = Field(str, mandatory=True)
    dose = Field(Or(str, int), mandatory=True)
    min_date = Field(datetime.date, mandatory=True)
    recommended_date = Field(datetime.date, mandatory=True)
    explanation = Field(str, mandatory=True)

class Contraindication(Fact):
    """Output fact: this vaccine is contraindicated for the patient."""
    vaccine = Field(str, mandatory=True)
    dose = Field(Or(str, int), mandatory=False)
    reason = Field(str, mandatory=True)
    explanation = Field(str, mandatory=True)

class CompletedSchedule(Fact):
    """Output fact: the vaccination schedule for this vaccine is complete/up to date."""
    vaccine = Field(str, mandatory=True)
    explanation = Field(str, mandatory=True)
    last_dose_date = Field(datetime.date, mandatory=False)

class ResolvedConflict(Fact):
    """Internal fact used to track resolved live-virus conflicts (e.g. SCR vs Febre Amarela)."""
    vaccines = Field([str], mandatory=True)
