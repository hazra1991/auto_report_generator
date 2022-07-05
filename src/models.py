from databasestore import DBConnect, Model,StringField,IntegerField

class TestRecord(Model):

    id = StringField('id',primary_key=True)
    rec_creation_data = StringField("rec_creation_data")
    module= StringField('module')
    total= IntegerField('total')
    passes =IntegerField('passes')
    pending=IntegerField('pending')
    failures=IntegerField('failures')
    duration =IntegerField('duration')
