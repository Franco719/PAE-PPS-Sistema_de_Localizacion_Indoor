from marshmallow import Schema, fields, validate


class ESP32ReceiverSchema(Schema):
    ssid = fields.Str(required=True, validate=validate.Length(min=1, max=32))
    bssid = fields.Str(required=True, validate=validate.Length(min=1, max=32))
    rssi = fields.Int(required=True, validate=validate.Range(min=-127, max=0))


class ESP32PayloadSchema(Schema):
    nodo_id = fields.Int(required=True, validate=validate.Range(min=1, max=10))
    networks = fields.List(fields.Nested(ESP32ReceiverSchema), required=True )


wifi_records_schema = ESP32PayloadSchema()