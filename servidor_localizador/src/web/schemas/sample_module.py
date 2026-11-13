from marshmallow import Schema, fields, validate, validates_schema, ValidationError

METHODS_WITH_WINDOW = {"Mean", "Median"}

class PreSampleSchema(Schema):

    room_name = fields.Str(required=True, validate=validate.Length(min=1, max=32))
    #filter_method = fields.Str(required=True,validate=validate.OneOf(["Kalman", "Median", "Mean", "Ninguno"]))
    window = fields.Integer(required=False, allow_none=True, validate=validate.Range(min=3, max=99))
    nodo_id = fields.Integer(required=True, allow_none=False, validate=validate.Range(min=1, max=10))

    @validates_schema
    def validate_window(self, data, **kwargs):

        #method = data["filter_method"]

        #if method in METHODS_WITH_WINDOW:

        window = data.get("window")

        if window is None:
            raise ValidationError(
                "La ventana es obligatoria para este método.",
                field_name="window"
            )

        if window % 2 == 0:
            raise ValidationError(
                "La ventana debe ser un número impar.",
                field_name="window"
            )
        
     
pre_sample_schema = PreSampleSchema()   
    