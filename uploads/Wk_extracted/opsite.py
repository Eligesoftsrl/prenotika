import mysql.connector as MySQLdb
import hashlib
import calendar
from azienda import Azienda
from prodotti import Prodotti
from datetime import datetime, date, timedelta
from proforma import Proforma
from cliente import Cliente
from campagna import Campagna
from pubblico import Pubblico
from nota import Nota
from team import Team
from news import News
from orari import Orari
from appuntamenti import Appuntamenti
import smtplib

global host_
#host_ = "Eligesoft.mysql.pythonanywhere-services.com"
host_ = "95.110.171.18"
global username_
#username_ = "Eligesoft"
username_ = "176_3475"
global password_
password_ = "pasq0378"
global database_
#database_ = "Eligesoft$eliboard"
database_ = "dbinstance_3475_1"

# --------------------------- METODI OPERATIVI -----------------------

def getID(tab):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT Id FROM "+tab+" ORDER BY Id DESC LIMIT 1"
        cursor = connection.cursor()
        cursor.execute(query);
        record = cursor.fetchone()
        if not record:
            myid=1
        else:
            myid = int(record[0])
            myid = myid+1

    except MySQLdb.Error as error:
            print("parameterized query failed {}".format(error))
            myid=0
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return myid




def setText(id,tabella,campo,valore):
    try:

        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "UPDATE "+tabella+" SET "+campo+" = %s WHERE Id = %s";
        tuple1 = (valore,id)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Eliminazione avvenuta con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di cancellazione"

    finally:

        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg


def setTextDinamico(id,tabella,campo,valore,idcampo):
    try:

        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "UPDATE "+tabella+" SET "+campo+" = %s WHERE "+idcampo+" = %s";
        tuple1 = (valore,id)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Eliminazione avvenuta con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di cancellazione"

    finally:

        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg


def setData(id,tabella,campo,valore):
        try:

            connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
            cursor = connection.cursor(prepared=True)
            valore = valore.replace("/","-")
            dt_object = datetime.strptime(valore, "%d-%m-%Y")
            query = "UPDATE "+tabella+" SET "+campo+" = %s WHERE Id = %s";
            tuple1 = (dt_object,id)
            cursor.execute(query,tuple1);
            connection.commit()
            msg = "Eliminazione avvenuta con successo"

        except MySQLdb.Error as error:
            print("parameterized query failed {}".format(error))
            msg = "Problemi durante la fase di cancellazione"

        finally:

            if connection.is_connected():
                cursor.close()
                connection.close()


        return msg


def euroformat(valore):
    amount = float(valore)
    currency = "€{:,.2f}".format(amount)

    return currency




def elimina(id,tabella):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "DELETE FROM "+tabella+" WHERE Id = %s";
        tuple1 = (id,)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Eliminazione avvenuta con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di cancellazione"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg

def elimina_dinamico(id,tabella,campo):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "DELETE FROM "+tabella+" WHERE "+campo+" = %s";
        tuple1 = (id,)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Eliminazione avvenuta con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di cancellazione"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg

def eliminacombo(id,tabella):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "DELETE FROM "+tabella+" WHERE Idd = %s";
        tuple1 = (id,)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Eliminazione avvenuta con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di cancellazione"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg

def elimina_page(id,tabella):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "DELETE FROM "+tabella+" WHERE Id = %s";
        tuple1 = (id,)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "ok"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "no"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg





def elimina_appuntamento(id,cliente,giorno,dal,al):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        g_object = datetime.strptime(giorno, "%d-%m-%Y")
        query = "DELETE FROM appuntamenti WHERE Iddoc = %s AND Cliente = %s AND Giorno = %s AND Dal = %s AND Al = %s ";
        tuple1 = (id,cliente,g_object,dal,al)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Eliminazione avvenuta con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di cancellazione"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg


# ------------------- GESTIONE AZIENDA ---------------------------


def nuova_azienda(nome,piva,sede,codice,telefono,email,referente,telefonoref,note,id,data):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO azienda VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)";
        tuple1 = (nome, piva, sede, codice, telefono, email, referente, telefonoref, note,id,data)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg


def getAllAziende():

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM azienda ORDER BY Data DESC"
        cursor = connection.cursor()
        cursor.execute(query);
        record = cursor.fetchall()
        for riga in record:
            riga_azienda = Azienda(riga[0],riga[1],riga[2],riga[3],riga[4],riga[5],riga[6],riga[7],riga[8],riga[9]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende



def getAzienda(id_azienda):

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM azienda WHERE Id = %s ORDER BY Ragione ASC"
        tuple1 = (id_azienda,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1);
        riga = cursor.fetchone()
        riga_azienda = Azienda(riga[0],riga[1],riga[2],riga[3],riga[4],riga[5],riga[6],riga[7],riga[8],riga[9]);



    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return riga_azienda




def Search_Azienda(mykey):
    lista_aziende=[]
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor()

        if mykey.isdigit() == True:
            query = "SELECT * FROM azienda WHERE Piva = '"+mykey+"'"
            cursor.execute(query);
        else:
            query = " SELECT * FROM azienda WHERE Ragione LIKE '%"+mykey+"%'"
            cursor.execute(query);

        record = cursor.fetchall()

        for riga in record:
            my_azienda = Azienda(riga[0],riga[1],riga[2],riga[3],riga[4],riga[5],riga[6],riga[7],riga[8],riga[9]);
            lista_aziende.append(my_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende


#----------------------------- GESTIONE PRODOTTI ------------------------

def getAllProdotti():
     lista_prodotti=[]
     try:
         connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
         query = "SELECT * FROM prodotti ORDER BY Descrizione ASC"
         cursor = connection.cursor()
         cursor.execute(query);
         record = cursor.fetchall()
         for riga in record:
             riga_prodotti = Prodotti(riga[0],riga[1],riga[2]);
             lista_prodotti.append(riga_prodotti)

     except MySQLdb.Error as error:
         print("parameterized query failed {}".format(error))

     finally:
         if connection.is_connected():
             cursor.close()
             connection.close()


     return lista_prodotti


def nuovo_prodotto(nome,prezzo,id):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO prodotti VALUES (%s,%s,%s)";
        tuple1 = (nome, prezzo, id)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg


def getProdotto(id_prodotto):

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM prodotti WHERE Id = %s ORDER BY Descrizione ASC"
        tuple1 = (id_prodotto,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1);
        riga = cursor.fetchone()
        riga_azienda = Prodotti(riga[0],riga[1],riga[2]);



    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return riga_azienda


#----------------------------- GESTIONE MATERIE ------------------------

def getAllMaterie():
     lista_prodotti=[]
     try:
         connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
         query = "SELECT * FROM materie ORDER BY Descrizione ASC"
         cursor = connection.cursor()
         cursor.execute(query);
         record = cursor.fetchall()
         for riga in record:
             riga_prodotti = Prodotti(riga[0],riga[1],riga[2]);
             lista_prodotti.append(riga_prodotti)

     except MySQLdb.Error as error:
         print("parameterized query failed {}".format(error))

     finally:
         if connection.is_connected():
             cursor.close()
             connection.close()


     return lista_prodotti


def nuova_materia(nome,prezzo,id):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO materie VALUES (%s,%s,%s)";
        tuple1 = (nome, prezzo, id)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg


def getMateria(id_prodotto):

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM materie WHERE Id = %s ORDER BY Descrizione ASC"
        tuple1 = (id_prodotto,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1);
        riga = cursor.fetchone()
        riga_azienda = Prodotti(riga[0],riga[1],riga[2]);



    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return riga_azienda


def getMaterieDoc(id_docente):

    try:
        lista_prodotti=[]
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM materie,combomat WHERE combomat.Idd = %s and materie.Prezzo = combomat.Materia ORDER BY materie.Descrizione ASC"
        tuple1 = (id_docente,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            riga_prodotti = Prodotti(riga[0],riga[1],riga[5]);
            lista_prodotti.append(riga_prodotti)



    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_prodotti


#----------------------------- GESTIONE MESSAGGI ------------------------

def getAllMessaggi():
     lista_prodotti=[]
     try:
         connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
         query = "SELECT * FROM messaggi ORDER BY Descrizione ASC"
         cursor = connection.cursor()
         cursor.execute(query);
         record = cursor.fetchall()
         for riga in record:
             riga_prodotti = Prodotti(riga[0],riga[1],riga[2]);
             lista_prodotti.append(riga_prodotti)

     except MySQLdb.Error as error:
         print("parameterized query failed {}".format(error))

     finally:
         if connection.is_connected():
             cursor.close()
             connection.close()


     return lista_prodotti


def nuovo_messaggio(nome,prezzo,id):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO messaggi VALUES (%s,%s,%s)";
        tuple1 = (nome, prezzo, id)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg


def getMessaggio(id_prodotto):

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM messaggi WHERE Id = %s ORDER BY Descrizione ASC"
        tuple1 = (id_prodotto,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1);
        riga = cursor.fetchone()
        riga_azienda = Prodotti(riga[0],riga[1],riga[2]);



    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return riga_azienda


#----------------------------- GESTIONE PROFORMA ------------------------



def nuova_proforma(azienda,data,importo,payment,descrizione,pagamento,note,id):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO proforma VALUES (%s,%s,%s,%s,%s,%s,%s,%s)";
        data = data.replace("/","-")
        dt_object = datetime.strptime(data, "%d-%m-%Y")
        tuple1 = (azienda,dt_object,importo,payment,descrizione,pagamento,note, id)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg

def getAllProforme():

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM proforma,azienda WHERE proforma.azienda = azienda.Id ORDER BY proforma.data DESC"
        cursor = connection.cursor()
        cursor.execute(query);
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            importo_ = euroformat(riga[2]);
            riga_azienda = Proforma(riga[0],miadata,importo_,riga[3],riga[4],riga[5],riga[6],riga[7],riga[8],riga[9]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende


def getProClient(id):

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM proforma,azienda WHERE azienda.Id = %s AND azienda.Id = proforma.azienda  ORDER BY proforma.data DESC"
        tuple1 = (id,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            importo_ = euroformat(riga[2]);
            riga_azienda = Proforma(riga[0],miadata,importo_,riga[3],riga[4],riga[5],riga[6],riga[7],riga[8],riga[9]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende


def nuovo_cliente(nome,cognome,residenza,cap,indirizzo,email,datan,cellulare,note,id,datai,sorgente):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO cliente VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)";
        data = datan.replace("/","-")
        dt_object = datetime.strptime(data, "%d-%m-%Y")
        tuple1 = (nome, cognome,residenza,cap,indirizzo,email,dt_object,cellulare,note,id,datai,sorgente)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg


def getAllClienti():

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM cliente ORDER BY Cognome ASC"
        cursor = connection.cursor()
        cursor.execute(query);
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[6]), "%Y-%m-%d").strftime("%d/%m/%Y")
            if miadata == "01/01/1900":
                miadata=''

            riga_azienda = Cliente(riga[0],riga[1],riga[2],riga[3],riga[4],riga[5],miadata,riga[7],riga[8],riga[9]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende


def getSmartClienti(query):

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor()
        cursor.execute(query);
        record = cursor.fetchall()
        for riga in record:
            riga_azienda = Cliente(riga[0],riga[1],riga[2],riga[3],riga[4],riga[5],riga[6],riga[7],riga[8],riga[9]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende

def getCliente(id):

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM cliente WHERE Id = %s ORDER BY Cognome ASC"
        tuple1 = (id,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1);
        riga = cursor.fetchone()
        miadata = datetime.strptime(str(riga[6]), "%Y-%m-%d").strftime("%d/%m/%Y")

        if miadata == "01/01/1900":
            miadata=''


        riga_azienda = Cliente(riga[0],riga[1],riga[2],riga[3],riga[4],riga[5],miadata,riga[7],riga[8],riga[9]);



    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return riga_azienda



def nuova_campagna(nome,testo,link,data,id):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO campagne VALUES (%s,%s,%s,%s,%s)";
        tuple1 = (nome, testo,link,data,id)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg


def nuovo_pubblico(idc,idp,id):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO pubblico VALUES (%s,%s,%s)";
        tuple1 = (idc,idp,id)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg


def getAllCampagne():

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM campagne ORDER BY Data DESC"
        cursor = connection.cursor()
        cursor.execute(query)
        record = cursor.fetchall()
        for riga in record:
            riga_azienda = Campagna(riga[0],riga[1],riga[2],riga[3],riga[4]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende


def getCampagna(id):

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM campagne WHERE Id = %s "
        tuple1 = (id,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1)
        riga = cursor.fetchone()
        miadata = datetime.strptime(str(riga[3]), "%Y-%m-%d").strftime("%d/%m/%Y")
        riga_azienda = Campagna(riga[0],riga[1],riga[2],miadata,riga[4]);



    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return riga_azienda


def getPubblico(id):
    pubblic_list=[]
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM pubblico WHERE pubblico.IdC = %s"
        tuple1 = (id,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1)
        record = cursor.fetchall()
        for riga in record:
            riga_azienda = Pubblico(riga[0],riga[1],riga[2])
            pubblic_list.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return  pubblic_list

def elimina_dal_pubblico(idc,idp,tabella):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "DELETE FROM "+tabella+" WHERE IdC = %s AND IdP= %s ";
        tuple1 = (idc,idp,)
        cursor.execute(query,tuple1)
        connection.commit()
        msg = "Eliminazione avvenuta con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di cancellazione"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg


def elimina_pubblico(idc,tabella):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "DELETE FROM "+tabella+" WHERE IdC = %s ";
        tuple1 = (idc,)
        cursor.execute(query,tuple1)
        connection.commit()
        msg = "Eliminazione avvenuta con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di cancellazione"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg


def nuova_nota(idc,testo,datai,tag,id):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO note VALUES (%s,%s,%s,%s,%s)";
        tuple1 = (idc,testo,datai,tag,id)
        cursor.execute(query,tuple1)
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg


def getNoteCliente(ida):

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM note WHERE Idc = %s ORDER BY Data DESC"
        cursor = connection.cursor()
        tuple1 = (ida,)
        cursor.execute(query,tuple1)
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[2]), "%Y-%m-%d").strftime("%d/%m/%Y")
            riga_azienda = Nota(riga[0],riga[1],miadata,riga[3],riga[4]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende




def nuovo_team(nome,cognome,username,password,email,cellulare,ruolo,id):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        hash = hashlib.md5(password.encode()).hexdigest()
        query = "INSERT INTO team VALUES (%s,%s,%s,%s,%s,%s,%s,%s)";
        tuple1 = (nome, cognome,username,hash,email,cellulare,ruolo,id)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg


def getAllTeam():

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM team ORDER BY Cognome ASC"
        cursor = connection.cursor()
        cursor.execute(query);
        record = cursor.fetchall()
        for riga in record:
            riga_azienda = Team(riga[0],riga[1],riga[2],riga[3],riga[4],riga[5],riga[6],riga[7]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende


def getTeam(id):

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM team WHERE Id = %s ORDER BY Cognome ASC"
        tuple1 = (id,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1);
        riga = cursor.fetchone()
        riga_azienda = Team(riga[0],riga[1],riga[2],riga[3],riga[4],riga[5],riga[6],riga[7]);



    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return riga_azienda


def getAuth(username,password):

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        hash = hashlib.md5(password.encode()).hexdigest()
        query = "SELECT * FROM team WHERE Username = %s AND Password= %s"
        tuple1 = (username,hash,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1);
        riga = cursor.fetchone()
        if riga:
            Id = riga[7]
        else:
            Id = 0


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return Id


def getPiva(piva):

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM azienda WHERE Piva = %s"
        tuple1 = (piva,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1);
        riga = cursor.fetchone()
        if riga:
            esito = True
        else:
            esito = False


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return esito




def nuova_news(titolo,testo,tipo,data,allegato,id):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO deal VALUES (%s,%s,%s,%s,%s,%s)";

        if data=='':
            data='01-01-1900'

        data = data.replace("/","-")
        dt_object = datetime.strptime(data, "%d-%m-%Y")
        tuple1 = (titolo,testo,tipo,dt_object,allegato,id)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg




def getAllNews():

        lista_aziende=[]

        try:
            connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
            query = "SELECT * FROM deal ORDER BY Data DESC"
            cursor = connection.cursor()
            cursor.execute(query);
            record = cursor.fetchall()
            for riga in record:
                miadata = datetime.strptime(str(riga[3]), "%Y-%m-%d").strftime("%d/%m/%Y")
                if miadata == '01/01/1900':
                    miadata=''

                riga_azienda = News(riga[0],riga[1],riga[2],miadata,riga[4],riga[5]);
                lista_aziende.append(riga_azienda)


        except MySQLdb.Error as error:
            print("parameterized query failed {}".format(error))

        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()


        return lista_aziende



def getNews(id):

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM deal WHERE Id = %s"
        tuple1 = (id,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1);
        riga = cursor.fetchone()
        miadata = datetime.strptime(str(riga[3]), "%Y-%m-%d").strftime("%d/%m/%Y")
        riga_azienda = News(riga[0],riga[1],riga[2],miadata,riga[4],riga[5]);


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return riga_azienda


def getGestore(id_azienda):

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM info_azienda WHERE Id = %s "
        tuple1 = (id_azienda,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1);
        riga = cursor.fetchone()
        riga_azienda = Azienda(riga[0],riga[4],riga[5],riga[6],riga[7],riga[1],riga[8],riga[2],riga[3],riga[9]);



    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return riga_azienda


def getCount(tabella,data):
    numero=0
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor()
        if tabella=='cliente' and data=='01-01-1900':
            query = "SELECT COUNT(*) FROM cliente"
            cursor.execute(query);
            myresult = cursor.fetchall()
            numero = myresult[-1][-1]


        elif tabella=='cliente' and data!='01-01-1900':
            query = "SELECT COUNT(*) FROM cliente WHERE DataI = %s "
            tuple1 = (data,)
            cursor.execute(query,tuple1);
            myresult = cursor.fetchall()
            numero = myresult[-1][-1]

        elif tabella=='docenti' and data=='01-01-1900':
            query = "SELECT COUNT(*) FROM docenti"
            cursor.execute(query);
            myresult = cursor.fetchall()
            numero = myresult[-1][-1]

        elif tabella=='docenti' and data!='01-01-1900':
            query = "SELECT COUNT(*) FROM docenti WHERE DataI = %s "
            tuple1 = (data,)
            cursor.execute(query,tuple1);
            myresult = cursor.fetchall()
            numero = myresult[-1][-1]

        elif tabella=='proforma':
            query = "SELECT COUNT(*) FROM proforma WHERE Data = %s "
            tuple1 = (data,)
            cursor.execute(query,tuple1);
            myresult = cursor.fetchall()
            numero = myresult[-1][-1]


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return numero




# ------------------- GESTIONE DOCENTI ---------------------------

def nuovo_docente(nome,cognome,residenza,cap,indirizzo,email,datan,cellulare,note,id,datai,sorgente):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO docenti VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)";
        data = datan.replace("/","-")
        dt_object = datetime.strptime(data, "%d-%m-%Y")
        tuple1 = (nome, cognome,residenza,cap,indirizzo,email,dt_object,cellulare,note,id,datai,sorgente)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg


def getAllDocenti():

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM docenti ORDER BY Cognome ASC"
        cursor = connection.cursor()
        cursor.execute(query);
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[6]), "%Y-%m-%d").strftime("%d/%m/%Y")
            if miadata == "01/01/1900":
                miadata=''
            riga_azienda = Cliente(riga[0],riga[1],riga[2],riga[3],riga[4],riga[5],miadata,riga[7],riga[8],riga[9]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende


def getSmartDocenti(query):

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor()
        cursor.execute(query);
        record = cursor.fetchall()
        for riga in record:
            riga_azienda = Cliente(riga[0],riga[1],riga[2],riga[3],riga[4],riga[5],riga[6],riga[7],riga[8],riga[9]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende

def getDocente(id):

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM docenti WHERE Id = %s ORDER BY Cognome ASC"
        tuple1 = (id,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1);
        riga = cursor.fetchone()
        miadata = datetime.strptime(str(riga[6]), "%Y-%m-%d").strftime("%d/%m/%Y")
        if miadata == "01/01/1900":
            miadata=''
        riga_azienda = Cliente(riga[0],riga[1],riga[2],riga[3],riga[4],riga[5],miadata,riga[7],riga[8],riga[9]);



    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return riga_azienda

def Search_Docente(mykey):
    lista_aziende=[]
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor()

        if mykey.isdigit() == True:
            query = "SELECT * FROM docenti WHERE Cellulare = '"+mykey+"'"
            cursor.execute(query);
        else:
            query = " SELECT * FROM docenti WHERE Nome LIKE '%"+mykey+"%' OR Cognome LIKE '%"+mykey+"%'"
            cursor.execute(query);

        record = cursor.fetchall()

        for riga in record:
            miadata = datetime.strptime(str(riga[6]), "%Y-%m-%d").strftime("%d/%m/%Y")
            my_azienda = Cliente(riga[0],riga[1],riga[2],riga[3],riga[4],riga[5],miadata,riga[7],riga[8],riga[9]);
            lista_aziende.append(my_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende

def newCombo(materia,id_docente,id):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO combomat VALUES (%s,%s,%s)";
        tuple1 = (materia,id_docente,id)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg

# -----------------GESTIONE ORARI--------------------


def nuovo_orario(id_docente,giorno,dal,al,id):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO orari VALUES (%s,%s,%s,%s,%s)";
        tuple1 = (id_docente, giorno, dal, al, id)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg

def getOrarioDocente(id_docente):

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM orari WHERE Idd= %s ORDER BY Id"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_docente,)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            riga_azienda = Orari(riga[0],riga[1],riga[2],riga[3],riga[4]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende


def getOrarioDocente_Giorno(id_docente,giorno):

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM orari WHERE Idd= %s AND Giorno = %s ORDER BY Dal ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_docente,giorno)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            riga_azienda = Orari(riga[0],riga[1],riga[2],riga[3],riga[4]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende


def getOrarioDocente_Giorno2(id_docente,giorno):

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM orari WHERE Idd= %s AND Giorno = %s ORDER BY Dal ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_docente,giorno)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            #riga_azienda = Orari(riga[0],riga[1],riga[2],riga[3],riga[4]);
            dal = riga[2]
            al = riga[3]
            lista_aziende.append([dal,al])


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende







def getSigleOrarioDocente(id):

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM orari WHERE Id= %s "
        cursor = connection.cursor(prepared=True)
        tuple1 = (id,)
        cursor.execute(query,tuple1);
        riga = cursor.fetchone()
        riga_azienda = Orari(riga[0],riga[1],riga[2],riga[3],riga[4]);



    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return riga_azienda


#-----------GESTIONE FERIE--------------

def getListaFerie(id_docente):

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM ferie WHERE Idd= %s ORDER BY Giorno ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_docente,)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            riga_azienda = Orari(riga[0],miadata,riga[2],riga[3],riga[4]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende


def nuove_ferie(id_docente,giorno,dal,al,id):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO ferie VALUES (%s,%s,%s,%s,%s)";
        data = giorno.replace("/","-")
        dt_object = datetime.strptime(data, "%d-%m-%Y")
        tuple1 = (id_docente, dt_object, dal, al, id)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg



def getDocenteMateria(materia):

    try:
        lista_aziende=[]
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM combomat,docenti WHERE combomat.Materia = %s and combomat.Idd = docenti.Id"
        tuple1 = (materia,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1);
        record = cursor.fetchall()

        for riga in record:
            miadata = datetime.strptime(str(riga[9]), "%Y-%m-%d").strftime("%d/%m/%Y")
            my_azienda = Cliente(riga[3],riga[4],riga[5],riga[6],riga[7],riga[8],miadata,riga[10],riga[11],riga[12]);
            lista_aziende.append(my_azienda)



    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende




def nuovo_appuntamento(id_docente,giorno,dal,al,alunno,note,id,idtext):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO appuntamenti VALUES (%s,%s,%s,%s,%s,%s,%s,%s)";

        dt_object = datetime.strptime(giorno, "%d-%m-%Y")
        tuple1 = (id_docente, dt_object, dal, al, alunno, note, id, idtext)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg



def nuovo_appuntamento_text(id_docente,giorno,dal,al,alunno,note,id):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO appuntamenti_text VALUES (%s,%s,%s,%s,%s,%s,%s)";

        dt_object = datetime.strptime(giorno, "%d-%m-%Y")
        tuple1 = (id_docente, dt_object, dal, al, alunno, note, id)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg

#--NON TOCCARE METODO PRIMARIO--

def getAppuntamenti(id_docente,giorno):

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM appuntamenti WHERE Iddoc= %s AND Giorno = %s ORDER BY Giorno,CONVERT(appuntamenti.Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_docente,giorno,)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            riga_azienda = Appuntamenti(riga[0],miadata,riga[2],riga[3],riga[4],riga[5],riga[6]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende

def getAppFromDay(id_docente,giorno):

    lista_aziende=[]
    currentDate = date.today()
    firstDayOfMonth = date(currentDate.year, currentDate.month, 1)
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM appuntamenti,cliente WHERE Iddoc= %s AND Giorno>= %s AND appuntamenti.cliente=cliente.id ORDER BY Giorno,CONVERT(appuntamenti.Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_docente,firstDayOfMonth)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            alunno = riga[7]+" "+riga[8]
            riga_azienda = Appuntamenti(riga[0],miadata,riga[2],riga[3],alunno,riga[5],riga[6]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende


def getTAppuntamento(id_app):

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM appuntamenti_text WHERE Id= %s ORDER BY Giorno,CONVERT(appuntamenti_text.Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_app,)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            riga_azienda = Appuntamenti(riga[0],miadata,riga[2],riga[3],riga[4],riga[5],riga[6]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende



def getTGAppuntamento(id_app,giorno):

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM appuntamenti_text WHERE Iddoc= %s AND Giorno = %s ORDER BY Giorno,CONVERT(appuntamenti_text.Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_app,giorno)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            riga_azienda = riga[2];
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende


def getSingleTGAppuntamento(id_app):

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM appuntamenti_text WHERE Id= %s ORDER BY Giorno,CONVERT(appuntamenti_text.Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_app,)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            print(miadata)
            riga_azienda = Appuntamenti(riga[0],miadata,riga[2],riga[3],riga[4],riga[5],riga[6]);
            lista_aziende.append(riga_azienda)

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende


def getStudentiApp(giorno,dal,al,docente):

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT cliente.nome,cliente.cognome FROM appuntamenti_text,cliente WHERE Giorno= %s AND Dal = %s AND Al = %s AND Iddoc = %s AND appuntamenti_text.cliente = cliente.Id"
        cursor = connection.cursor(prepared=True)
        tuple1 = (giorno,dal,al,docente,)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            ragsoc = riga[0]+" "+riga[1]
            lista_aziende.append(ragsoc)

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende


def getAppDocDay(id_docente,giorno):

    lista_aziende=[]
    currentDate = date.today()
    firstDayOfMonth = date(currentDate.year, currentDate.month, 1)
    lastDayOfMonth = date(currentDate.year, currentDate.month, calendar.monthrange(currentDate.year, currentDate.month)[1])

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM appuntamenti_text,cliente WHERE Iddoc= %s AND Giorno >= %s AND Giorno<= %s AND appuntamenti_text.cliente=cliente.id ORDER BY Giorno,CONVERT(appuntamenti_text.Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_docente,firstDayOfMonth,lastDayOfMonth)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            alunno = riga[7]+" "+riga[8]
            riga_azienda = Appuntamenti(riga[0],miadata,riga[2],riga[3],alunno,riga[5],riga[6]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende

def getAppDocDayG(id_docente,giorno):

    lista_aziende=[]
    currentDate = date.today()
    firstDayOfMonth = date(currentDate.year, currentDate.month, 1)
    lastDayOfMonth = date(currentDate.year, currentDate.month, calendar.monthrange(currentDate.year, currentDate.month)[1])
    week = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']


    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM appuntamenti_text,cliente WHERE Iddoc= %s AND Giorno >= %s AND Giorno<= %s AND appuntamenti_text.cliente=cliente.id ORDER BY Giorno,CONVERT(appuntamenti_text.Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_docente,firstDayOfMonth,lastDayOfMonth)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            desc_day = week[riga[1].weekday()]
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            miadata = desc_day+" | "+miadata
            alunno = riga[7]+" "+riga[8]
            riga_azienda = Appuntamenti(riga[0],miadata,riga[2],riga[3],alunno,riga[5],riga[6]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende

def getAppDocRange(id_docente,dal,al):

    lista_aziende=[]
    currentDate = date.today()
    dal = dal.replace("/","-")
    al = al.replace("/","-")
    dal_object = datetime.strptime(dal, "%d-%m-%Y")
    al_object = datetime.strptime(al, "%d-%m-%Y")
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM appuntamenti_text,cliente WHERE Iddoc= %s AND Giorno>= %s AND Giorno<= %s AND appuntamenti_text.cliente=cliente.id ORDER BY Giorno,CONVERT(appuntamenti_text.Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_docente,dal_object,al_object)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            alunno = riga[7]+" "+riga[8]
            riga_azienda = Appuntamenti(riga[0],miadata,riga[2],riga[3],alunno,riga[5],riga[6]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende



def getAppDocRangeG(id_docente,dal,al):

    lista_aziende=[]
    week = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    currentDate = date.today()
    dal = dal.replace("/","-")
    al = al.replace("/","-")
    dal_object = datetime.strptime(dal, "%d-%m-%Y")
    al_object = datetime.strptime(al, "%d-%m-%Y")
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM appuntamenti_text,cliente WHERE Iddoc= %s AND Giorno>= %s AND Giorno<= %s AND appuntamenti_text.cliente=cliente.id ORDER BY Giorno,CONVERT(appuntamenti_text.Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_docente,dal_object,al_object)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            desc_day = week[riga[1].weekday()]
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            miadata = desc_day+" | "+miadata
            alunno = riga[7]+" "+riga[8]
            riga_azienda = Appuntamenti(riga[0],miadata,riga[2],riga[3],alunno,riga[5],riga[6]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende

def getAppCliente(id_cliente,giorno):

    lista_aziende=[]
    currentDate = date.today()
    firstDayOfMonth = date(currentDate.year, currentDate.month, 1)
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM appuntamenti_text,docenti WHERE appuntamenti_text.cliente = %s AND Giorno>= %s AND appuntamenti_text.Iddoc=docenti.id ORDER BY Giorno,CONVERT(appuntamenti_text.Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_cliente,currentDate,)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            docente = riga[7]+" "+riga[8]
            riga_azienda = Appuntamenti(riga[0],miadata,riga[2],riga[3],docente,riga[5],riga[6]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende



def getAppClienteG(id_cliente,giorno):

    lista_aziende=[]
    week = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    currentDate = date.today()
    firstDayOfMonth = date(currentDate.year, currentDate.month, 1)
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM appuntamenti_text,docenti WHERE appuntamenti_text.cliente = %s AND Giorno>= %s AND appuntamenti_text.Iddoc=docenti.id ORDER BY Giorno,CONVERT(appuntamenti_text.Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_cliente,currentDate,)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            desc_day = week[riga[1].weekday()]
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            miadata = desc_day+" | "+miadata
            docente = riga[7]+" "+riga[8]
            riga_azienda = Appuntamenti(riga[0],miadata,riga[2],riga[3],docente,riga[5],riga[6]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende




def getAppCliRange(id_cliente,dal,al):

    lista_aziende=[]
    currentDate = date.today()
    dal = dal.replace("/","-")
    al = al.replace("/","-")
    dal_object = datetime.strptime(dal, "%d-%m-%Y")
    al_object = datetime.strptime(al, "%d-%m-%Y")
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM appuntamenti_text,docenti WHERE appuntamenti_text.cliente = %s AND Giorno>= %s AND Giorno<= %s  AND appuntamenti_text.Iddoc=docenti.id ORDER BY Giorno,CONVERT(appuntamenti_text.Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_cliente,dal_object,al_object,)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            docente = riga[7]+" "+riga[8]
            riga_azienda = Appuntamenti(riga[0],miadata,riga[2],riga[3],docente,riga[5],riga[6]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende



def getAppCliRangeG(id_cliente,dal,al):

    lista_aziende=[]
    week = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    currentDate = date.today()
    dal = dal.replace("/","-")
    al = al.replace("/","-")
    dal_object = datetime.strptime(dal, "%d-%m-%Y")
    al_object = datetime.strptime(al, "%d-%m-%Y")
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM appuntamenti_text,docenti WHERE appuntamenti_text.cliente = %s AND Giorno>= %s AND Giorno<= %s  AND appuntamenti_text.Iddoc=docenti.id ORDER BY Giorno,CONVERT(appuntamenti_text.Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_cliente,dal_object,al_object,)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            desc_day = week[riga[1].weekday()]
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            docente = riga[7]+" "+riga[8]
            miadata = desc_day+" | "+miadata
            riga_azienda = Appuntamenti(riga[0],miadata,riga[2],riga[3],docente,riga[5],riga[6]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende


def getMeseCliente(id_cliente):

    lista_aziende=[]
    currentDate = date.today()
    firstDayOfMonth = date(currentDate.year, currentDate.month, 1)
    lastDayOfMonth = date(currentDate.year, currentDate.month, calendar.monthrange(currentDate.year, currentDate.month)[1])
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM appuntamenti_text,docenti WHERE appuntamenti_text.cliente = %s AND Giorno>= %s AND Giorno<= %s AND appuntamenti_text.Iddoc=docenti.id ORDER BY Giorno,CONVERT(appuntamenti_text.Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_cliente,firstDayOfMonth,lastDayOfMonth,)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            docente = riga[7]+" "+riga[8]
            riga_azienda = Appuntamenti(riga[0],miadata,riga[2],riga[3],docente,riga[5],riga[6]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende




def nuovo_conteggio(id_cliente,ore,status,giorno,id):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO conteggio VALUES (%s,%s,%s,%s,%s)";
        #dt_object = datetime.strptime(giorno, "%d-%m-%Y")
        tuple1 = (id_cliente, ore, status, giorno, id)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg


def getConteggio(id_cliente):

    rigatab=""

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM conteggio WHERE Idc= %s ORDER BY Data ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_cliente,)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[3]), "%Y-%m-%d").strftime("%d-%m-%Y")
            rigatab=rigatab+"<tr><td>"+riga[1]+"</td><td>"+riga[2]+"</td><td>"+miadata+"</td><td><a href=\"#\">ELIMINA</a></td></tr>"



    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return rigatab


def getOreConteggio(id_cliente):

    rigatab=""

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM conteggio WHERE Idc= %s ORDER BY Data ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (id_cliente,)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:

            rigatab=riga[1]



    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return rigatab

def getDailyPlan(giorno):

    lista_aziende=[]

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM appuntamenti_text,cliente,docenti WHERE Giorno= %s AND appuntamenti_text.cliente=cliente.id AND appuntamenti_text.Iddoc=docenti.id ORDER BY appuntamenti_text.Iddoc,CONVERT(appuntamenti_text.Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (giorno,)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        for riga in record:
            miadata = datetime.strptime(str(riga[1]), "%Y-%m-%d").strftime("%d-%m-%Y")
            alunno = riga[7]+" "+riga[8]
            docente = riga[19]+" "+riga[20]
            riga_azienda = Appuntamenti(docente,miadata,riga[2],riga[3],alunno,riga[5],riga[6]);
            lista_aziende.append(riga_azienda)


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende

def getVerApp(giorno,docente,dal,al):

    lista_aziende=""
    giorno = giorno.replace("/","-")
    giorno_object = datetime.strptime(giorno, "%d-%m-%Y")

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT * FROM appuntamenti_text WHERE Giorno= %s AND Iddoc=%s AND Dal=%s AND Al=%s  ORDER BY Iddoc,CONVERT(appuntamenti_text.Dal,Time) ASC"
        #query = "SELECT * FROM appuntamenti WHERE Giorno= %s AND Iddoc=%s AND (CONVERT(Dal,Time)<=CONVERT(%s,Time) AND CONVERT(Al,Time)>=CONVERT(%s,Time))  ORDER BY Iddoc,CONVERT(Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (giorno_object,docente,dal,al)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()

        if record:
            lista_aziende = "si"
        else:
            lista_aziende = "no"


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende


#INTERVALLO DI MINUTI

def getIntervallo(id_docente):
    intervallo = ""
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT Minuti FROM intervalli WHERE Idd = %s"
        tuple1 = (id_docente,)
        cursor = connection.cursor()
        cursor.execute(query,tuple1);
        riga = cursor.fetchone()
        if riga:
            intervallo = riga[0]



    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return intervallo


def nuovaFrazione(id_docente,min,id):
    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        cursor = connection.cursor(prepared=True)
        query = "INSERT INTO intervalli VALUES (%s,%s,%s)";
        #dt_object = datetime.strptime(giorno, "%d-%m-%Y")
        tuple1 = (id_docente, min, id)
        cursor.execute(query,tuple1);
        connection.commit()
        msg = "Inserimento avvenuto con successo"

    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))
        msg = "Problemi durante la fase di Inserimento"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return msg



def getStuApp(giorno,docente,dal):

    lista_aziende=""
    giorno = giorno.replace("/","-")
    giorno_object = datetime.strptime(giorno, "%d-%m-%Y")

    try:
        connection = MySQLdb.connect(host = host_ ,user = username_ , password = password_ ,database = database_)
        query = "SELECT cliente.Nome,cliente.cognome,cliente.Id FROM appuntamenti,cliente WHERE Giorno= %s AND Iddoc=%s AND Dal=%s AND appuntamenti.Cliente = cliente.Id ORDER BY Iddoc,CONVERT(appuntamenti.Dal,Time) ASC"
        cursor = connection.cursor(prepared=True)
        tuple1 = (giorno_object,docente,dal,)
        cursor.execute(query,tuple1);
        record = cursor.fetchall()
        if record:
            for riga in record:
                ragsoc = riga[0]+" "+riga[1]+"<hr>"
                lista_aziende = lista_aziende + ragsoc
        else:
            lista_aziende = ""


    except MySQLdb.Error as error:
        print("parameterized query failed {}".format(error))

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


    return lista_aziende
