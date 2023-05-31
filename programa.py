import psycopg2
from datetime import *
from peewee import *
from funcions import ahora , data_entrada
from bdd import bdd_base

'''importar base de dades'''
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
        

def busqueda_coche(busqueda_matricula):
    #busqueda de la matricula si existe o no en la base de datos
    #entrada de matricula
    #salida si existe o no en bool
    bdd_agenda.connect()
    query = bdd_agenda.execute_sql("select matricula from estacionamientos e inner join plazas ON e.plaza_id = plazas.id where plazas.estado = 'SI' and e._import_total = 0.00 and e.matricula = %s", (busqueda_matricula,))

    for y in query:  
        if y[0] == busqueda_matricula:         
            return True
        else:
            return False


def salida_coche_menu():
    '''imprimir un menu de la salida de parking'''
    print ("\n")
    print('hoy: ', ahora())
    print("has de seleccionar 1 a 5")
    print("1. Import que ha de pagar.")
    print("2. Donades una data i una hora, el número de places ocupades.")
    print("3. l’historial d’estacionaments a l’aparcament de la matricula.")
    print("4. llistat de les deu places més ocupades durant la data")
    print("5. Sortir del menu")
    print()


def entrada_coche_menu():
    '''imprimir un menu de la entrada de parking'''
    print ("\n")
    print('hoy: ', ahora())
    print("has de seleccionar 1 a 5")
    print("1. Reservar una entrada per el coche")
    print("2. Obtenir el número de places disponibles.")
    print("3. Obtenir el número de places ocupades.")
    print("4. l’historial d’estacionaments a l’aparcament de la plaça.")
    print("5. Sortir del menu")
    print()

def is_list_empty(list):
    # chekear la lista si esta vacia
    # entrada de lista
    # salida si esta vacia o esta llena
    if len(list) == 0:
        return True
    return False



if  __name__ == '__main__':

    while (True):
        matricula_guardar = ""
        salir = False

        matricula_guardar = input ("Posa la matricula: ")
        '''salida de coche'''
        if busqueda_coche(matricula_guardar) == True:
            print ("la matricula existeix , que vols fer : ")
            while salir != True:
                salida_coche_menu() 
                opcio = int(input())
                if opcio == 1:
                
                    '''comprovar el estado que nunca ha sido pagado y ademas obtiene todos los datos para poder hacer un update''' 
                    comprovante_import = estacionamientos.select().where(
                        estacionamientos._import_total == 0.00 and estacionamientos.matricula == matricula_guardar).get()    
                    '''si todo ha ido bien , hara los cambios , sino el programa compta que el vechicle ja ha pagat 
                    el import y hauria de fer una nova entrada'''   

                    if comprovante_import._import_total == 0.0:

                        '''hace el update de la salida del coche si al final sale'''            
                        estacionamientos.update(fecha_hora_salida = ahora() ).where(
                            estacionamientos.matricula == matricula_guardar).execute()
                        
                        '''calcular los minutos , dias , hores lo que ha estado el coche'''
                        dias_en_aparcamiento = ahora() - data_entrada(str(comprovante_import.fecha_hora_entrada)) 
                        minutos = int(dias_en_aparcamiento.total_seconds() / 60)

                        '''calcula el import total'''
                        _import_total_ = round(minutos * comprovante_import.importe , 2)

                        '''hace el update del import total , asi nos indica el coche ya ha salido'''
                        estacionamientos.update(_import_total = _import_total_ ).where(
                            estacionamientos.matricula == matricula_guardar).execute()
                        
                        '''cambiar el estado de la plaza para que este disponible otra vez'''
                        plazas.update(estado = 'NO').where(plazas.id == comprovante_import.plaza_id).execute()
                        print ("has de pagar: " , _import_total_  , "€")
                    else : 
                        print ("el coche ja esta pagat , gracies per la teva visita")
                        
                elif opcio == 2:
                    '''tendria que poner la fecha que quiere buscar , 
                    tiene que ser en este formato , 
                    lo he dificultado pero la aplicacion no saldra hasta que se ponga bien'''
                    lista = []
                    comprobar_fecha = True
                    print ("posa una fecha i una hora para mostrar las plazas que han sido ocupadas")
                    while comprobar_fecha == True:
                        try:
                            fecha = input ("las fehca debe ser en este formato 2000-04-16 08:09:00 \n")
                            '''he puesto varibales a las fechas asi para que no den errores a la hora de compilacion'''
                            fecha_fecha = data_entrada(fecha)
                            fecha_mas_hora = fecha_fecha + timedelta(hours= 1)      
                            string = str(fecha_mas_hora)
                            query = estacionamientos.select((estacionamientos.plaza_id + 1).alias("plaza_id")).where((estacionamientos.fecha_hora_entrada >= str(fecha_fecha)) & (estacionamientos.fecha_hora_entrada <= string) ).execute()   
                            '''poner los resultado de la query'''                   
                            for i in query:                
                                lista.append("Plaza: "  + str(i.plaza_id))

                            '''comprobar si la lista esta vacia o no'''
                            if is_list_empty(lista) == True:
                                print ("no ha habido plazas ocupadas en esta hora" , fecha_fecha)
                            else: 
                                print("las plazas que han sido ocupadas durante esta fehca y esta hora :")
                                print (lista)

                            comprobar_fecha = False

                        except ValueError:
                            print("Fecha inválida")
                       

                elif opcio == 3:
                    '''busca la fecha que han entrado los coches y los guarda en una lista i al final los muestra , si no existe hace un print'''
                    query = estacionamientos.select(estacionamientos.fecha_hora_entrada).where(estacionamientos.matricula == matricula_guardar)
                    lista = []
                    for i in query:

                        lista.append("fechas: "  + str(i.fecha_hora_entrada))

                    if is_list_empty(lista) == True:
                        print ("no ha habido fechas ocupadas por la  matricula de : " , matricula_guardar )
                    else: 
                        print("las fechas que han sido ocupadas de esta matricla :")
                        print (lista)

                elif opcio == 4:
                    '''busca las 10 plazas mas ocupadas y los muestra en el for'''
                    query2 = (estacionamientos.select(estacionamientos.plaza_id, fn.Count(estacionamientos.plaza_id)
                                                    .alias("counted")).group_by(estacionamientos.plaza_id)
                                                    .order_by(fn.Count(estacionamientos.plaza_id).desc())
                                                    .limit(10)
                                                    .execute())
                    for i in query2:
                        print ("plaza:" , str(i.plaza_id) , ", ocupaciones:" , str(i.counted))

                elif opcio == 5:
                    salir = True
                    bdd_agenda.close()
        
        else:      
            '''entrada de coche'''
            print ("la matricula no existeix , Que vols fer : ")
            while salir != True:
                entrada_coche_menu() 
                opcio = int(input())
                if opcio == 1:
                    '''reservar plaza'''  
                    salir_reserva = False
                    while (not salir_reserva):
                        plaza = int(input("que plaza quieres reservar: "))

                        '''coger informacion desde la base de datos , tambien recogo informacion del mes para saber los precios del mes'''
                        mes = ahora().strftime('%m')
                        _importe = preus.select(preus.preus_minut).where(preus.mes == mes).get()
                        _estado = plazas.select(plazas.estado).where(plazas.numero == plaza).get()
        
                        '''si el estado de la plaza esta vacio , hace el registro y si no , la plaza dira que esta ocupada'''
                        if _estado.estado == "NO":
                            '''busca la id para despues sumarle mas uno y registrar-lo en el insert'''
                            _id = estacionamientos.select(estacionamientos.id).order_by(estacionamientos.id.desc()).limit(1).get()
                            '''hacemos el insert en la base de datos poniendo todos los datos que hemos obtenido desde la base de datos'''
                            bdd_agenda.execute_sql("INSERT INTO estacionamientos (id, matricula, plaza_id, importe) VALUES (" + str(_id.id + 1) + ", '" + matricula_guardar + "', " + str(plaza - 1) + ", " + str(_importe.preus_minut) + ")")
                            '''hacemos un update a la plaza para que se quede ocupada'''
                            query = plazas.update(estado = "SI").where(plazas.numero == plaza).execute()
                            print ("S'ha reservat la plaza correctament")
                            salir_reserva = True
                            salir = True

                            bdd_agenda.close()
                        else : print ("la plaza esta ocupada , vuelve a introdocir otra plaza")
                        
                elif opcio == 2:
                    '''plazas disponibles'''    
                    query = plazas.select().where(plazas.estado == 'NO')
                    lista = []
                    print ("plazas disponibles: ")
                    count = 1
                    for i in query:
                        if count % 5 == 0:   
                            print( "plaza: " , str(i.numero)  )
                        else: print( "plaza: " + str(i.numero) , end=" | " )
                        count += 1

                elif opcio == 3:
                    '''plazas ocupadas'''  
                    query = plazas.select().where(plazas.estado == 'SI')
                    lista =[] 
                    count = 1         
                    print ("plazas ocupadas: ")
                    for i in query:
                        if count % 5 == 0:   
                            print( "plaza: " , str(i.numero)  )
                        else: print( "plaza: " + str(i.numero) , end=" | " )
                        count += 1


                elif opcio == 4:
                    '''las fehcas que ha estado ocupada dicha plaza'''
                    plaza = int(input("pon la plaza que quieres buscasr para mostarar los registros de la plaza: "))      
                    query = estacionamientos.select(estacionamientos.matricula , estacionamientos.fecha_hora_entrada).join(plazas).where(plazas.numero == plaza)
                    print ("las fechas con la matricula que ha estado ocupado la plaza es : \n")
                    for i in query:
                        print (i.matricula , ": " , i.fecha_hora_entrada)

                elif opcio == 5:
                    salir = True
                    bdd_agenda.close() 