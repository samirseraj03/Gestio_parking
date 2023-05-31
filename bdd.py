from peewee import *

def bdd_base():
    bdd_agenda = PostgresqlDatabase( 'gestion_parking_db',user='postgres',password='aref1310', host='192.168.18.103',port=5432)   
    class BaseModel(Model):
        class Meta:
            database = bdd_agenda
    class plazas(BaseModel):
            id = AutoField()
            numero = IntegerField()
            estado = TextField()

    class estacionamientos(BaseModel):
            id = AutoField()
            fecha_hora_entrada = DateTimeField()
            fecha_hora_salida = DateTimeField()
            matricula = CharField()
            plaza_id = ForeignKeyField(plazas)
            importe = DoubleField()
            _import_total = DoubleField()

    class preus(BaseModel):
            id = AutoField()
            mes = IntegerField()
            preus_minut = DoubleField()