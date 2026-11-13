from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class PreTrainingSchema(Schema):
    
    filter_method = fields.Str(required=True,validate=validate.OneOf(["Kalman", "Median", "Mean", "Ninguno"]))
    training_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    
class ChangeNameSchema(Schema):

    new_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))

    
pre_training_schema = PreTrainingSchema()
change_name_schema = ChangeNameSchema()