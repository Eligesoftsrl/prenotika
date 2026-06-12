from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.utils import secure_filename
import os
import mysql.connector as MySQLdb
from azienda import Azienda
from prodotti import Prodotti
import opsite as op
from proforma import Proforma
from datetime import datetime, date, timedelta
from cliente import Cliente
from pubblico import Pubblico
from nota import Nota
from team import Team
from orari import Orari
from Wk import Wk
from appuntamenti import Appuntamenti
import hashlib


app = Flask(__name__)
app.secret_key="eligesoftpy"
app.permanent_session_lifetime = timedelta(days=5)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif', '.pdf']
app.config['UPLOAD_PATH'] = 'static/upload'



@app.route("/")
def index():
   if "Nome" in session:
       today = datetime.today()
       #tot_cli = op.getCount("cliente","01-01-1900")
       #tot_cli_oggi = op.getCount("cliente",today)
       #tot_az = op.getCount("docenti","01-01-1900")
       #tot_az_oggi = op.getCount("docenti",today)
       #tot_pro_oggi = op.getCount("proforma",today)
       #return render_template("index.html",tot_cli = tot_cli,tot_cli_oggi=tot_cli_oggi,tot_az = tot_az,tot_az_oggi=tot_az_oggi,tot_pro_oggi=tot_pro_oggi)
       return render_template("index.html")
   else:
       return render_template('Login.html',titolo="Accedi ora")


@app.route("/login", methods=('GET','POST'))
def login():
    if request.method == 'POST':
        username = request.form.get('Username')
        password = request.form.get('Password')
        idteam = op.getAuth(username,password)
        if idteam!=0:
            myteam = op.getTeam(idteam)
            session["Nome"] = myteam.nome
            session["Cognome"] = myteam.cognome
            session["Ruolo"] = myteam.ruolo
            today = datetime.today()
            #tot_cli = op.getCount("cliente","01-01-1900")
            #tot_cli_oggi = op.getCount("cliente",today)
            #tot_az = op.getCount("azienda","01-01-1900")
            #tot_az_oggi = op.getCount("azienda",today)
            #tot_pro_oggi = op.getCount("proforma",today)
            #return render_template("index.html",tot_cli = tot_cli,tot_cli_oggi=tot_cli_oggi,tot_az = tot_az,tot_az_oggi=tot_az_oggi,tot_pro_oggi=tot_pro_oggi)
            return render_template("index.html")
        else:
            msg="Accesso Fallito."
            return render_template("Login.html", titolo=msg)


@app.route("/logout")
def logout():
    session.pop("Nome",None)
    session.pop("Cognome",None)
    session.pop("Ruolo",None)
    return render_template('Login.html',titolo="Accedi ora")


@app.route("/register", methods=('GET','POST'))
def register():
    if request.method == 'POST':
        nome = request.form.get('Nome')
        cognome = request.form.get('Cognome')
        email= request.form.get("Email")
        datan = request.form.get("DataN")

        if datan=="":
            datan="01/01/1900"

        cellulare = request.form.get("Cellulare")
        id = op.getID("cliente")
        residenza = ""
        cap = ""
        indirizzo = ""
        note = "";
        msg = op.nuovo_cliente(nome,cognome,residenza,cap,indirizzo,email,datan,cellulare,note,id)

    return render_template("Register.html", titolo=msg)

@app.route("/Registrazione")
def registrazione():
    return render_template("Register.html", titolo="Iscriviti ora")


@app.route("/new_azienda")
def new_azienda():
    return render_template("Azienda.html")


@app.route('/create', methods=('GET','POST'))
def create():
    if request.method == 'POST':
        ragione = request.form.get('Ragione')
        piva = request.form.get('Piva')
        sede = request.form.get('Sede')
        codicef = request.form.get("CodiceF")
        telefono = request.form.get("Telefono")
        email= request.form.get("Email")
        referente = request.form.get("Referente")
        telefonor = request.form.get("TelefonoR")
        note = request.form.get("Note")
        today = datetime.today()
        id = op.getID("azienda")
        msg = op.nuova_azienda(ragione,piva,sede,codicef,telefono,email,referente,telefonor,note,id,today)
        return render_template('Azienda.html', risposta=msg)


@app.route("/lista_aziende", methods=('GET','POST'))
def lista_aziende():
    aziende = op.getAllAziende()
    return render_template("Lista.html",aziende=aziende)


@app.route('/<int:ida>/elimina', methods=('GET','POST'))
def elimina(ida):
    msg = op.elimina(ida,"azienda")
    return redirect('/lista_aziende')

@app.route('/<int:ida>/modifica', methods=('GET','POST'))
def modifica(ida):
    az = op.getAzienda(ida)
    return render_template('Edit-Azienda.html', azienda=az, risposta="")

@app.route('/<int:ida>/edit', methods=('GET','POST'))
def edit(ida):
    if request.method == 'POST':
        ragione = request.form.get('Ragione')
        op.setText(ida,"azienda","Ragione",ragione)
        piva = request.form.get('Piva')
        op.setText(ida,"azienda","Piva",piva)
        sede = request.form.get('Sede')
        op.setText(ida,"azienda","Sede",sede)
        codicef = request.form.get("CodiceF")
        op.setText(ida,"azienda","Codicef",codicef)
        telefono = request.form.get("Telefono")
        op.setText(ida,"azienda","Telefono",telefono)
        email= request.form.get("Email")
        op.setText(ida,"azienda","Email",email)
        referente = request.form.get("Referente")
        op.setText(ida,"azienda","Referente",referente)
        telefonor = request.form.get("TelefonoR")
        op.setText(ida,"azienda","TelefonoR",telefonor)
        note = request.form.get("Note")
        op.setText(ida,"azienda","Note",note)
        az = op.getAzienda(ida)
        msg = "Modifica Eseguita con successo"

    return render_template('/Edit-Azienda.html', azienda=az, risposta=msg)


@app.route('/cerca', methods=('GET','POST'))
def cerca():
    if request.method == 'POST':
        ricerca = request.form.get('Search')
        ris_az = op.Search_Docente(ricerca)
        return render_template("Lista.html",clienti=ris_az, risposa="")


@app.route('/prodotti')
def prodotti():
    lista_pro = op.getAllProdotti()
    return render_template("Prodotti.html", listapro = lista_pro)


@app.route('/nuovo_prodotto', methods=('GET','POST'))
def nuovo_prodotto():
    if request.method == 'POST':
        descrizione = request.form.get('Descrizione')
        prezzo = request.form.get('Prezzo')
        id = op.getID("prodotti")
        msg = op.nuovo_prodotto(descrizione,prezzo,id)
        return redirect('/prodotti')


@app.route('/<int:ida>/elimina_prodotto', methods=('GET','POST'))
def elimina_prodotto(ida):
    msg = op.elimina(ida,"prodotti")
    return redirect('/prodotti')


@app.route('/<int:ida>/modifica_prodotto', methods=('GET','POST'))
def modifica_prodotto(ida):
    az = op.getProdotto(ida)
    return render_template('Edit-Prodotto.html', prodotto=az)



@app.route('/<int:ida>/edit_prodotto', methods=('GET','POST'))
def edit_prodotto(ida):
    if request.method == 'POST':
        descrizione = request.form.get('Descrizione')
        op.setText(ida,"prodotti","Descrizione",descrizione)
        prezzo = request.form.get('Prezzo')
        op.setText(ida,"prodotti","Prezzo",prezzo)

        msg = "Modifica Eseguita con successo"

        az = op.getMateria(ida)

    return render_template('Edit-Materia.html', prodotto=az,risposta=msg)


#-----------------MATERIE-------------------

@app.route('/materie')
def materie():
    lista_pro = op.getAllMaterie()
    return render_template("Materie.html", listapro = lista_pro, risposta="")


@app.route('/nuova_materia', methods=('GET','POST'))
def nuova_materia():
    if request.method == 'POST':
        descrizione = request.form.get('Descrizione')

        prezzo = request.form.get('Prezzo')


    if descrizione=="":
        msg=""
    else:
        id = op.getID("materie")
        if prezzo == "":
            prezzo = str(id)

        msg = op.nuova_materia(descrizione,prezzo,id)

    lista_pro = op.getAllMaterie()
    return render_template("Materie.html", listapro = lista_pro, risposta=msg)


@app.route('/<int:ida>/elimina_materia', methods=('GET','POST'))
def elimina_materia(ida):
    mat = op.getMateria(ida)
    codice = mat.prezzo
    msg = op.elimina(ida,"materie")
    if msg=='Eliminazione avvenuta con successo':
        op.elimina_dinamico(codice,"combomat","Materia")

    lista_pro = op.getAllMaterie()
    return render_template("Materie.html", listapro = lista_pro, risposta=msg)


@app.route('/<int:ida>/modifica_materia', methods=('GET','POST'))
def modifica_materia(ida):
    az = op.getMateria(ida)
    return render_template('Edit-Materia.html', prodotto=az)



@app.route('/<int:ida>/edit_materia', methods=('GET','POST'))
def edit_materia(ida):
    if request.method == 'POST':
        descrizione = request.form.get('Descrizione')
        prezzo = request.form.get('Prezzo')

    if descrizione=="":
        msg="La descrizione della materia non può essere vuota"
    else:
        op.setText(ida,"materie","Descrizione",descrizione)
        #op.setText(ida,"materie","Prezzo",prezzo)
        msg = "Modifica Eseguita con successo<br><a href=\"/materie\">Visualizza la lista completa</a><br>"

    az = op.getMateria(ida)

    return render_template('Edit-Materia.html', prodotto=az,risposta=msg)












#-----------------MESSAGGI-------------------

@app.route('/messaggi')
def messaggi():
    lista_pro = op.getAllMessaggi()
    return render_template("Messaggi.html", listapro = lista_pro, risposta="")


@app.route('/nuovo_messaggio', methods=('GET','POST'))
def nuovo_messaggio():
    if request.method == 'POST':
        descrizione = request.form.get('Descrizione')

        prezzo = request.form.get('Prezzo')


    if descrizione=="":
        msg=""
    else:
        id = op.getID("messaggi")
        if prezzo == "":
            prezzo = str(id)

        msg = op.nuovo_messaggio(descrizione,prezzo,id)

    lista_pro = op.getAllMessaggi()
    return render_template("Messaggi.html", listapro = lista_pro, risposta=msg)


@app.route('/<int:ida>/elimina_messaggio', methods=('GET','POST'))
def elimina_messaggio(ida):
    mat = op.getMessaggio(ida)
    codice = mat.prezzo
    msg = op.elimina(ida,"messaggi")
    #if msg=='Eliminazione avvenuta con successo':
    #    op.elimina_dinamico(codice,"combomat","Materia")

    lista_pro = op.getAllMessaggi()
    return render_template("Messaggi.html", listapro = lista_pro, risposta=msg)


@app.route('/<int:ida>/modifica_messaggio', methods=('GET','POST'))
def modifica_messaggio(ida):
    az = op.getMessaggio(ida)
    return render_template('Edit-Messaggi.html', prodotto=az)



@app.route('/<int:ida>/edit_messaggio', methods=('GET','POST'))
def edit_messaggio(ida):
    if request.method == 'POST':
        descrizione = request.form.get('Descrizione')
        prezzo = request.form.get('Prezzo')

    if descrizione=="":
        msg="Il testo del messaggio non può essere vuoto"
    else:
        op.setText(ida,"messaggi","Descrizione",descrizione)
        #op.setText(ida,"materie","Prezzo",prezzo)
        msg = "Modifica Eseguita con successo<br><a href=\"/messaggi\">Visualizza la lista completa</a><br>"

    az = op.getMessaggio(ida)

    return render_template('Edit-Messaggi.html', prodotto=az,risposta=msg)


@app.route('/invia_sms', methods=('GET','POST'))
def invia_sms():
    if request.method == 'POST':
        testo = request.form.get('Testo')

        mobile = request.form.getlist('CheckT')
        if mobile:
            for x in range(len(mobile)):
                print("Telefono: "+mobile[x])


    lista_compleanni=[]
    clienti = op.getAllClienti()
    datetime_object = date.today()
    miadata = datetime.strptime(str(datetime_object), "%Y-%m-%d").strftime("%d-%m-%Y")
    t_day = str(datetime_object.day)
    t_mese = str(datetime_object.month)

    for cli in clienti:
        datan = cli.datan
        mese = datan[3:5]
        if '0' in mese and mese !='10':
            mese = mese[1:2]

        giorno = datan[0:2]
        anno = datan[6:-1]

        if anno != "1900":
            if giorno==t_day and mese==t_mese:
                lista_compleanni.append(cli)


    lista_pro = op.getAllMessaggi()
    return render_template("Compleanni.html",clienti=lista_compleanni,today=miadata,listapro=lista_pro)











@app.route('/<int:ida>/new_invoice')
def new_invoice(ida):
    az = op.getAzienda(ida)
    lista_pro = op.getAllProdotti()
    today = datetime.today()
    d1 = today.strftime("%d/%m/%Y")
    return render_template('/Invoice.html', azienda=az, listapro=lista_pro, today=d1)


@app.route('/new_proforma', methods=('GET','POST'))
def new_proforma():
    if request.method == 'POST':
        azienda = request.form.get("azienda")
        data = request.form.get("data")
        importo = request.form.get("importo")
        payment = request.form.get("payment")
        descrizione = request.form.get('descrizione')
        pagamento = request.form.get('pagamento')
        note = request.form.get('note')
        id = op.getID("proforma")
        msg = op.nuova_proforma(azienda,data,importo,payment,descrizione,pagamento,note,id)
        return render_template('/Result.html', risposta=msg)


@app.route("/lista_proforme", methods=('GET','POST'))
def lista_proforme():
    proforme = op.getAllProforme()
    return render_template("Lista_Proforme.html",proforme=proforme,titolo="tutte le proforme")



@app.route('/<int:ida>/proforme_azienda', methods=('GET','POST'))
def proforme_azienda(ida):

    azienda = op.getAzienda(ida)
    ragsoc = azienda.nome
    titolo = "tutte le proforme di "+ragsoc
    proforme = op.getProClient(ida)
    return render_template("Lista_Proforme.html",proforme=proforme,titolo=titolo)


#--------------------GESTIONE CLIENTI ----------------------

@app.route('/nuovo_cliente')
def nuovo_cliente():
    empty=""
    return render_template("Cliente.html",risposta=empty)


@app.route('/crea_cliente', methods=('GET','POST'))
def crea_cliente():
    if request.method == 'POST':
        nome = request.form.get('Nome')
        cognome = request.form.get('Cognome')
        residenza = request.form.get('Residenza')
        cap = request.form.get("Cap")
        indirizzo = request.form.get("Indirizzo")
        email= request.form.get("Email")
        datan = request.form.get("DataN")
        if datan=="":
            datan="01/01/1900"
        cellulare = request.form.get("Cellulare")
        note = request.form.get("Note")
        id = op.getID("cliente")
        fonte = request.form.get("Fonte")
        today = datetime.today()
        msg = op.nuovo_cliente(nome,cognome,residenza,cap,indirizzo,email,datan,cellulare,note,id,today,fonte)
        if msg=="Inserimento avvenuto con successo":
            msg="<b>Inserimento avvenuto con successo</b><br>"
            msg=msg+"<b style=\"font-size:22px;\"><a href=\"/trova_docente\"><i class=\"bx bx-right-arrow-alt\"></i>&nbsp;Inserisci Appuntamento</a></b><br><br>"

        return render_template('Cliente.html', risposta=msg)



@app.route("/lista_clienti", methods=('GET','POST'))
def lista_clienti():
    clienti = op.getAllClienti()
    risposta=""
    return render_template("Listaclienti.html",clienti=clienti,risposta=risposta)


@app.route('/<int:ida>/elimina_cliente', methods=('GET','POST'))
def elimina_cliente(ida):
    msg = op.elimina(ida,"cliente")
    if msg=='Eliminazione avvenuta con successo':
        op.elimina_dinamico(ida,"note","Idc")
        op.elimina_dinamico(ida,"appuntamenti","Cliente")
        op.elimina_dinamico(ida,"appuntamenti_text","Cliente")
        op.elimina_dinamico(ida,"conteggio","Idc")


    clienti = op.getAllClienti()
    return render_template("Listaclienti.html",clienti=clienti,risposta=msg)

@app.route('/<int:ida>/edit_cliente', methods=('GET','POST'))
def edit_cliente(ida):
    if request.method == 'POST':
        nome = request.form.get('Nome')
        op.setText(ida,"cliente","Nome",nome)
        cognome = request.form.get('Cognome')
        op.setText(ida,"cliente","Cognome",cognome)
        residenza = request.form.get('Residenza')
        op.setText(ida,"cliente","Residenza",residenza)
        cap = request.form.get("Cap")
        op.setText(ida,"cliente","Cap",cap)
        indirizzo = request.form.get("Indirizzo")
        op.setText(ida,"cliente","Indirizzo",indirizzo)
        email= request.form.get("Email")
        op.setText(ida,"cliente","Email",email)
        datan = request.form.get("DataN")
        if datan=='':
            datan='01/01/1900'

        op.setData(ida,"cliente","DataN",datan)

        cellulare = request.form.get("Cellulare")
        op.setText(ida,"cliente","Cellulare",cellulare)
        note = request.form.get("Note")
        op.setText(ida,"cliente","Note",note)
        msg = "Modifica Eseguita con successo"


    cli = op.getCliente(ida)
    return render_template('Edit-Cliente.html', cliente=cli,risposta=msg)



@app.route('/<int:ida>/modifica_cliente', methods=('GET','POST'))
def modifica_cliente(ida):
    risposta=""
    cli = op.getCliente(ida)
    return render_template('Edit-Cliente.html', cliente=cli,risposta=risposta)



@app.route("/compleanni", methods=('GET','POST'))
def compleanni():
    lista_compleanni=[]
    clienti = op.getAllClienti()
    datetime_object = date.today()
    miadata = datetime.strptime(str(datetime_object), "%Y-%m-%d").strftime("%d-%m-%Y")
    t_day = str(datetime_object.day)
    t_mese = str(datetime_object.month)

    for cli in clienti:
        datan = cli.datan
        mese = datan[3:5]
        if '0' in mese and mese !='10':
            mese = mese[1:2]

        giorno = datan[0:2]
        anno = datan[6:-1]

        if anno != "1900":
            if giorno==t_day and mese==t_mese:
                lista_compleanni.append(cli)


    lista_pro = op.getAllMessaggi()
    return render_template("Compleanni.html",clienti=lista_compleanni,today=miadata,listapro=lista_pro)


@app.route('/nuova_campagna')
def nuova_campagna():
    empty=""
    return render_template("Campagna.html",risposta=empty)

@app.route('/crea_campagna', methods=('GET','POST'))
def crea_campagna():
    if request.method == 'POST':

        nomec = request.form.get('NomeC')
        testoc = request.form.get('TestoC')
        link = request.form.get('Link')
        datetime_object = date.today()
        id = op.getID("campagne")
        msg = op.nuova_campagna(nomec,testoc,link,datetime_object,id)

        if msg == "Inserimento avvenuto con successo":

            nome = request.form.get('Nome')
            residenza = request.form.get('Residenza')
            cap = request.form.get("Cap")
            datan = request.form.get("DataN")
            if datan=="":
                datan="01/01/1900"

            count=0
            query="SELECT * FROM cliente";

            if nome!="" or residenza!="" or cap!="" or datan!="":

                if nome !="":
                    if count==0:
                        query=query+" WHERE nome='"+nome+"'"
                        count+= 1
                    else:
                        query=query+" AND nome='"+nome+"'"
                        count+= 1

                if residenza != "":
                    if count==0:
                        query=query+" WHERE residenza LIKE '"+residenza+"'"
                        count+= 1
                    else:
                        query=query+" AND residenza LIKE '"+residenza+"'"
                        count+= 1


                if cap !="":
                    if count==0:
                        query=query+" WHERE cap='"+cap+"'"
                        count+= 1
                    else:
                        query=query+" AND cap='"+cap+"'"
                        count+= 1

                risultato = op.getSmartClienti(query)

                for ris in risultato:
                    idec = ris.id
                    idet = op.getID("pubblico")
                    msg = op.nuovo_pubblico(id,idec,idet)

            else:
                risultato = op.getAllClienti()

                for ris in risultato:
                    idec = ris.id
                    idet = op.getID("pubblico")
                    msg = op.nuovo_pubblico(id,idec,idet)




        return render_template("Campagna.html",risposta=msg)



@app.route("/lista_campagne", methods=('GET','POST'))
def lista_campagne():
    campagne = op.getAllCampagne()
    risposta=""
    return render_template("Listacampagne.html",campagne=campagne,risposta=risposta)


@app.route('/<int:ida>/modifica_campagna', methods=('GET','POST'))
def modifica_campagna(ida):

    risposta=""
    tabella=[]
    campagna = op.getCampagna(ida)
    pubblic = op.getPubblico(ida)
    for pub in pubblic:
        cliente_id = pub.idc
        cli = op.getCliente(cliente_id)
        tabella.append(cli)


    return render_template('Edit-Campagna.html', campagna=campagna,tabella=tabella,risposta=risposta)


@app.route('/<int:idc>/<int:idp>/elimina_persona', methods=('GET','POST'))
def elimina_persona(idp,idc):
    msg = op.elimina_dal_pubblico(idc,idp,"pubblico")
    tabella=[]
    campagna = op.getCampagna(idc)
    pubblic = op.getPubblico(idc)
    for pub in pubblic:
        cliente_id = pub.idc
        cli = op.getCliente(cliente_id)
        tabella.append(cli)

    return render_template('Edit-Campagna.html', campagna=campagna,tabella=tabella,risposta=msg)


@app.route('/<int:ida>/edit_campagna', methods=('GET','POST'))
def edit_campagna(ida):
    if request.method == 'POST':

        nome = request.form.get('NomeC')
        op.setText(ida,"campagne","Nome",nome)
        testo = request.form.get('TestoC')
        op.setText(ida,"campagne","Testo",testo)
        link = request.form.get('Link')
        op.setText(ida,"campagne","Link",link)

        msg = "Modifica Eseguita con successo"


    tabella=[]
    campagna = op.getCampagna(ida)
    pubblic = op.getPubblico(ida)
    for pub in pubblic:
        cliente_id = pub.idc
        cli = op.getCliente(cliente_id)
        tabella.append(cli)

    return render_template('Edit-Campagna.html', campagna=campagna,tabella=tabella,risposta=msg)


@app.route("/<int:ida>/elimina_campagna", methods=('GET','POST'))
def elimina_campagna(ida):
    msg = op.elimina(ida,"campagne")
    msg_ = op.elimina_pubblico(ida,"campagne")
    campagne = op.getAllCampagne()
    return render_template("Listacampagne.html",campagne=campagne,risposta=msg)


@app.route('/<int:ida>/nuova_nota')
def nuova_nota(ida):
    cliente = op.getCliente(ida)
    lista_pro = op.getAllProdotti()
    empty=""
    return render_template("Nota.html",risposta=empty,cliente=cliente,tags=lista_pro)

@app.route('/crea_nota', methods=('GET','POST'))
def crea_nota():
    if request.method == 'POST':
        nota = request.form.get('Note')
        idc = request.form.get('Idcliente')
        datetime_object = date.today()
        tag = request.form.get('Tag')
        id = op.getID("note")
        msg = op.nuova_nota(idc,nota,datetime_object,tag,id)
        cliente = op.getCliente(idc)
        lista_pro = op.getAllProdotti()
        return render_template("Nota.html",risposta=msg,cliente=cliente,tags=lista_pro)

@app.route('/<int:ida>/lista_note')
def lista_note(ida):
    note = op.getNoteCliente(ida)
    cliente = op.getCliente(ida)
    empty=""
    return render_template("ListaNote.html",risposta=empty,note=note,cliente=cliente)

@app.route('/<int:ida>/elimina_nota')
def elimina_nota(ida):

    msg = op.elimina(ida,"note")
    note = op.getNoteCliente(ida)
    cliente = op.getCliente(ida)
    empty=""
    return render_template("ListaNote.html",risposta=msg,note=note,cliente=cliente)



#--------------------GESTIONE TEAM ----------------------

@app.route('/nuovo_team')
def nuovo_team():
    empty=""
    return render_template("Team.html",risposta=empty)


@app.route('/crea_team', methods=('GET','POST'))
def crea_team():
    if request.method == 'POST':
        nome = request.form.get('Nome')
        cognome = request.form.get('Cognome')
        username = request.form.get('Username')
        password = request.form.get("Password")
        email = request.form.get("Email")
        cellulare = request.form.get("Cellulare")
        ruolo = request.form.get("Ruolo")
        id = op.getID("team")
        msg = op.nuovo_team(nome,cognome,username,password,email,cellulare,ruolo,id)
        return render_template('Team.html', risposta=msg)



@app.route("/lista_team", methods=('GET','POST'))
def lista_team():
    clienti = op.getAllTeam()
    risposta=""
    return render_template("Listateam.html",clienti=clienti,risposta=risposta)


@app.route('/<int:ida>/elimina_team', methods=('GET','POST'))
def elimina_team(ida):
    msg = op.elimina(ida,"team")
    clienti = op.getAllTeam()
    return render_template("Listateam.html",clienti=clienti,risposta=msg)

@app.route('/<int:ida>/edit_team', methods=('GET','POST'))
def edit_team(ida):
    if request.method == 'POST':

        nome = request.form.get('Nome')
        op.setText(ida,"team","Nome",nome)

        cognome = request.form.get('Cognome')
        op.setText(ida,"team","Cognome",cognome)

        username = request.form.get('Username')
        op.setText(ida,"team","Username",username)

        password = request.form.get("Password")
        if(password!=""):
            hash = hashlib.md5(password.encode()).hexdigest()
            op.setText(ida,"team","Password",hash)

        email= request.form.get("Email")
        op.setText(ida,"team","Email",email)

        cellulare = request.form.get("Cellulare")
        op.setText(ida,"team","Cellulare",cellulare)

        ruolo= request.form.get("Ruolo")
        op.setText(ida,"team","Ruolo",ruolo)

        msg = "Modifica Eseguita con successo"


    cli = op.getTeam(ida)
    return render_template('Edit-Team.html', cliente=cli,risposta=msg)



@app.route('/<int:ida>/modifica_team', methods=('GET','POST'))
def modifica_team(ida):
    risposta=""
    cli = op.getTeam(ida)
    return render_template('Edit-Team.html', cliente=cli,risposta=risposta)



@app.route('/verifica_piva', methods=('GET','POST'))
def verifica_piva():
    if request.method == 'POST':
        piva = request.form.get('Piva')
        esito = op.getPiva(piva)
        if esito == True:
            return jsonify({'output':'Partita Iva già presente in archivio. Azienda già registrata.'})
        else:
            return jsonify({'output':''})

        return render_template('Azienda.html', risposta="")



#--------------------GESTIONE PROMO ----------------------


@app.route('/nuova_news')
def nuova_news():
    empty=""
    today = datetime.today()
    d1 = today.strftime("%d/%m/%Y")
    return render_template("News.html",risposta=empty,day=d1)


@app.route('/crea_news', methods=('GET','POST'))
def crea_news():
    if request.method == 'POST':
        titolo = request.form.get('Titolo')
        testo = request.form.get('Testo')
        tipologia = request.form.get('Tipologia')
        data = request.form.get("Data")

        uploaded_file = request.files['file']
        filename = secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                filename=""
            uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))

        id = op.getID("deal")
        msg = op.nuova_news(titolo,testo,tipologia,data,filename,id)
        today = datetime.today()
        d1 = today.strftime("%d/%m/%Y")
        return render_template('News.html', risposta=msg, day=d1)



@app.route("/lista_news", methods=('GET','POST'))
def lista_news():
    news= op.getAllNews()
    risposta=""
    return render_template("Listanews.html",news=news,risposta=risposta)



@app.route('/<int:ida>/edit_news', methods=('GET','POST'))
def edit_news(ida):
    if request.method == 'POST':

        titolo = request.form.get('Titolo')
        op.setText(ida,"deal","Titolo",titolo)

        testo = request.form.get('Testo')
        op.setText(ida,"deal","Testo",testo)

        tipologia = request.form.get('Tipologia')
        op.setText(ida,"deal","Tipologia",tipologia)

        data = request.form.get("Data")
        if data=='':
            data='01/01/1900'

        op.setData(ida,"deal","Data",data)

        uploaded_file = request.files['file']
        filename = secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                filename=""
            uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
            op.setText(ida,"deal","Allegato",filename)


        msg = "Modifica Eseguita con successo"
        news = op.getNews(ida)


    return render_template('Edit-News.html', news=news, risposta=msg)


@app.route('/<int:ida>/elimina_news', methods=('GET','POST'))
def elimina_news(ida):
    msg = op.elimina(ida,"deal")
    news = op.getAllNews()

    return render_template("Listanews.html",news=news,risposta=msg)


@app.route('/<int:ida>/modifica_news', methods=('GET','POST'))
def modifica_news(ida):
    news = op.getNews(ida)
    return render_template("Edit-News.html",news=news,risposta='')




#--------------------DATI GESTORE ----------------------


@app.route('/<int:ida>/edit_gestore', methods=('GET','POST'))
def edit_gestore(ida):
    if request.method == 'POST':

        ragione = request.form.get('Ragione')
        op.setText(ida,"info_azienda","Ragsoc",ragione)

        piva = request.form.get('Piva')
        op.setText(ida,"info_azienda","Piva",piva)

        sede = request.form.get('Sede')
        op.setText(ida,"info_azienda","Sede",sede)

        facebook = request.form.get("Facebook")
        op.setText(ida,"info_azienda","Facebook",facebook)

        email= request.form.get("Email")
        op.setText(ida,"info_azienda","Email",email)

        instagram = request.form.get("Instagram")
        op.setText(ida,"info_azienda","Instagram",instagram)

        web = request.form.get("Web")
        op.setText(ida,"info_azienda","Web",web)

        newsletter = request.form.get("Newsletter")
        op.setText(ida,"info_azienda","Newsletter",newsletter)

        paypal = request.form.get("Paypal")
        op.setText(ida,"info_azienda","Paypal",paypal)


        msg = "Modifica Eseguita con successo"

        azienda = op.getGestore(ida)


    return render_template('Edit-Gestore.html', azienda=azienda, risposta=msg)


@app.route('/<int:ida>/modifica_gestore', methods=('GET','POST'))
def modifica_gestore(ida):
    azienda = op.getGestore(ida)
    return render_template("Edit-Gestore.html",azienda=azienda,risposta='')


#--------------------GESTIONE DOCENTI ----------------------

@app.route('/nuovo_docente')
def nuovo_docente():
    empty=""
    lista_mat = op.getAllMaterie()
    return render_template("Docente.html",risposta=empty,listamat=lista_mat)


@app.route('/crea_docente', methods=('GET','POST'))
def crea_docente():
    id = 0
    if request.method == 'POST':
        nome = request.form.get('Nome')
        cognome = request.form.get('Cognome')
        residenza = request.form.get('Residenza')
        cap = request.form.get("Cap")
        indirizzo = request.form.get("Indirizzo")
        email= request.form.get("Email")
        datan = request.form.get("DataN")
        if datan=="":
            datan="01/01/1900"
        cellulare = request.form.get("Cellulare")
        note = request.form.get("Note")
        id = op.getID("docenti")
        fonte = request.form.get("Fonte")
        frazione = request.form.get("Frazione")
        today = datetime.today()
        msg = op.nuovo_docente(nome,cognome,residenza,cap,indirizzo,email,datan,cellulare,note,id,today,fonte)
        if msg == "Inserimento avvenuto con successo":
            selezione = request.form.getlist('Materie')
            if selezione:
                for sel in selezione:
                    idt = op.getID("combomat")
                    op.newCombo(sel,id,idt)

            idi = op.getID("intervalli")
            op.nuovaFrazione(id,frazione,idi)

        lista_mat = op.getAllMaterie()
        msg="<b>Inserimento avvenuto con successo</b><br>"
        msg=msg+"<b style=\"font-size:22px;\"><a href=\"/"+str(id)+"/gest_orario\"><i class=\"bx bx-right-arrow-alt\"></i>&nbsp;Inserisci adesso gli orari di lavoro</a></b><br><br>"

        return render_template('Docente.html', risposta=msg,listamat=lista_mat)



@app.route("/lista_docenti", methods=('GET','POST'))
def lista_docenti():
    clienti = op.getAllDocenti()
    risposta=""
    return render_template("Lista.html",clienti=clienti,risposta=risposta)


@app.route('/<int:ida>/elimina_docente', methods=('GET','POST'))
def elimina_docenti(ida):
    msg = op.elimina(ida,"docenti")
    if msg=='Eliminazione avvenuta con successo':
        op.elimina_dinamico(ida,"combomat","Idd")
        op.elimina_dinamico(ida,"appuntamenti","Iddoc")
        op.elimina_dinamico(ida,"appuntamenti_text","Iddoc")
        op.elimina_dinamico(ida,"orari","Idd")
        op.elimina_dinamico(ida,"ferie","Idd")


    clienti = op.getAllDocenti()
    return render_template("Lista.html",clienti=clienti,risposta=msg)

@app.route('/<int:ida>/edit_docente', methods=('GET','POST'))
def edit_docente(ida):
    if request.method == 'POST':
        nome = request.form.get('Nome')
        op.setText(ida,"docenti","Nome",nome)
        cognome = request.form.get('Cognome')
        op.setText(ida,"docenti","Cognome",cognome)
        residenza = request.form.get('Residenza')
        op.setText(ida,"docenti","Residenza",residenza)
        cap = request.form.get("Cap")
        op.setText(ida,"docenti","Cap",cap)
        indirizzo = request.form.get("Indirizzo")
        op.setText(ida,"docenti","Indirizzo",indirizzo)
        email= request.form.get("Email")
        op.setText(ida,"docenti","Email",email)
        datan = request.form.get("DataN")
        if datan=='':
            datan='01/01/1900'

        op.setData(ida,"docenti","DataN",datan)
        cellulare = request.form.get("Cellulare")
        op.setText(ida,"docenti","Cellulare",cellulare)
        note = request.form.get("Note")
        op.setText(ida,"docenti","Note",note)

        min =  request.form.get("Frazione")
        op.setTextDinamico(ida,"intervalli","Minuti",min,"Idd")

        msg = "Modifica Eseguita con successo"
        selezione = request.form.getlist('Materie')
        if selezione:
            op.eliminacombo(ida,"combomat")
            for sel in selezione:
                idt = op.getID("combomat")
                op.newCombo(sel,ida,idt)

    cli = op.getDocente(ida)
    mat = op.getMaterieDoc(ida)
    lista_mat = op.getAllMaterie()
    frazione = op.getIntervallo(ida)
    frazione = "<option value=\""+frazione+"\">-- "+frazione+"min --</option>"

    opzione=""

    for item in lista_mat:
        codice = item.prezzo

        verifica=""
        for mysel in mat:
            mycodice = mysel.prezzo

            if mycodice == codice:
                verifica="ok"
                break

        if verifica=='ok':
            opzione = opzione+"<option value='"+item.prezzo+"' selected>"+item.nome+"</option>"
        else:
            opzione = opzione+"<option value='"+item.prezzo+"'>"+item.nome+"</option>"

    return render_template('Edit-Docente.html', cliente=cli, risposta=msg, materie=opzione,frazione=frazione)



@app.route('/<int:ida>/modifica_docente', methods=('GET','POST'))
def modifica_docente(ida):
    risposta=""
    selezione=""
    cli = op.getDocente(ida)
    mat = op.getMaterieDoc(ida)
    frazione = op.getIntervallo(ida)
    frazione = "<option value=\""+frazione+"\">-- "+frazione+"min --</option>"
    lista_mat = op.getAllMaterie()
    for item in lista_mat:
        codice = item.prezzo

        verifica=""
        for mysel in mat:
            mycodice = mysel.prezzo

            if mycodice == codice:
                verifica="ok"
                break

        if verifica=='ok':
            selezione = selezione+"<option value='"+item.prezzo+"' selected>"+item.nome+"</option>"
        else:
            selezione = selezione+"<option value='"+item.prezzo+"'>"+item.nome+"</option>"

    return render_template('Edit-Docente.html', cliente=cli,risposta=risposta,materie=selezione,frazione=frazione)





#------------GESTIONE ORARI E DATE -----------

@app.route('/<int:ida>/gest_orario', methods=('GET','POST'))
def gest_orario(ida):
    msg = ""
    lista_orari = op.getOrarioDocente(ida)
    return render_template("Orari.html",risposta=msg,orari = lista_orari,id_doc=ida)


@app.route('/<int:ida>/nuovo_orario', methods=('GET','POST'))
def nuovo_orario(ida):
    if request.method == 'POST':
        giorno = request.form.getlist('Giorni')
        dal = request.form.get('Dal')
        al = request.form.get('Al')
        if giorno:
         for x in range(len(giorno)):
             id = op.getID("orari")
             msg = op.nuovo_orario(ida,giorno[x],dal,al,id)
        else:
            msg = "Oops! Forse hai dimenticato di selezionare almeno un giorno.Riprova."

    lista_orari = op.getOrarioDocente(ida)
    return render_template("Orari.html",risposta=msg,orari = lista_orari,id_doc=ida)


@app.route('/<int:idd>/<int:ida>/elimina_orario', methods=('GET','POST'))
def elimina_orario(idd,ida):
    msg = op.elimina(ida,"orari")
    lista_orari = op.getOrarioDocente(idd)
    return render_template("Orari.html",risposta=msg,orari = lista_orari,id_doc=idd)

@app.route('/<int:idd>/<int:ida>/modifica_orario', methods=('GET','POST'))
def modifica_orario(idd,ida):
    if request.method == 'POST':
        giorno = request.form.get('Giorni')
        msg = op.setText(ida,"orari","Giorno",giorno)
        dal = request.form.get('Dal')
        msg =op.setText(ida,"orari","Dal",dal)
        al = request.form.get('Al')
        msg =op.setText(ida,"orari","Al",al)

    lista_orari = op.getOrarioDocente(idd)
    return render_template("Orari.html",risposta=msg,orari = lista_orari,id_doc=idd)


@app.route('/<int:idd>/<int:ida>/edit_orario', methods=('GET','POST'))
def edit_orario(idd,ida):
    lista_orari = op.getOrarioDocente(idd)
    orario = op.getSigleOrarioDocente(ida)
    return render_template("Edit-Orari.html", risposta="", orari = lista_orari, id_doc=idd, single=orario)


#------------GESTIONE FESTIVITA -----------

@app.route('/<int:ida>/gest_ferie', methods=('GET','POST'))
def gest_ferie(ida):
    msg = ""
    lista_orari = op.getListaFerie(ida)
    return render_template("Ferie.html",risposta=msg, orari = lista_orari,id_doc=ida)


@app.route('/<int:ida>/nuove_ferie', methods=('GET','POST'))
def nuove_ferie(ida):
    if request.method == 'POST':
        giorno = request.form.get('Giorni')
        dal = request.form.get('Dal')
        al = request.form.get('Al')
        id = op.getID("ferie")
        msg = op.nuove_ferie(ida,giorno,dal,al,id)
        lista_orari = op.getListaFerie(ida)
    return render_template("Ferie.html",risposta=msg,orari = lista_orari,id_doc=ida)

@app.route('/<int:idd>/<int:ida>/elimina_ferie', methods=('GET','POST'))
def elimina_ferie(idd,ida):
    msg = op.elimina(ida,"ferie")
    lista_orari = op.getListaFerie(idd)
    return render_template("Ferie.html",risposta=msg,orari = lista_orari,id_doc=idd)


#------- AAPUNTAMENTI ---------
@app.route('/cerca_docente', methods=('GET','POST'))
def cerca_docente():
    msg = ""
    listapro = op.getAllMaterie()
    return render_template("CercaMaterie.html", risposta=msg, listapro = listapro)

@app.route('/trova_docente', methods=('GET','POST'))
def trova_docente():
    msg = ""
    listapro = op.getAllDocenti()
    return render_template("CercaDocente.html", risposta=msg, listapro = listapro)

@app.route('/go_week', methods=('GET','POST'))
def go_week():
    docente=""
    msg = ""
    if request.method == 'POST':
        docente =  request.form.get('Selezione')

    if docente=="":
        listapro = op.getAllDocenti()
        msg="Docente non selezionato!"
        return render_template("CercaDocente.html", risposta=msg, listapro = listapro)
    else:
        return redirect("/"+docente+"/settimana_docente")






@app.route('/materia_docente', methods=('GET','POST'))
def materia_docente():
    msg = ""
    listapro = op.getAllMaterie()
    if request.method == 'POST':
        materia = request.form.get('Materia')
        lista_prof  = op.getDocenteMateria(materia)

    return render_template("VisDoc.html", risposta=msg, listapro = listapro, clienti = lista_prof)




#-----------METODI PER CALENDARIO--------

def free_time(x,bounds,time):
        new=[]
        ultimo = len(bounds)-1
        b_start=datetime.strptime(bounds[0],"%H:%M")

        b_end=datetime.strptime(bounds[ultimo],"%H:%M")

        start=datetime.strptime(x[0][0],"%H:%M")

        end=datetime.strptime(x[len(x)-1][1],"%H:%M")

        min_start=(b_start-start).seconds/60

        min_end=(b_end-end).seconds/60

        if start>b_end:
            new.append([bounds[0],bounds[ultimo]])
        else:
            if min_start >= float(time):
                new.append([bounds[0],x[0][0]])
            for i in range(len(x)-1):
                if ((datetime.strptime(x[i+1][0],"%H:%M")-datetime.strptime(x[i][1],"%H:%M")).seconds/60) >=float(time):
                    new.append([x[i][1],x[i+1][0]])

            if min_end >= float(time):
                new.append([x[len(x)-1][1],bounds[ultimo]])

        return new

def interval_time(lista_ore,min):
    intervallo=[]
    for ore in lista_ore:
        start = datetime.strptime(ore[0], "%H:%M")
        end = datetime.strptime(ore[1], "%H:%M")
        delta = timedelta(minutes=min)
        t = start
        while t <= end:
            intervallo.append([datetime.strftime(t, '%H:%M'),datetime.strftime(t+delta, '%H:%M')])
            t += delta

    return intervallo

def interval_time_single(lista_ore,min):
        intervallo=[]
        for ore in lista_ore:
            start = datetime.strptime(ore[0], "%H:%M")
            end = datetime.strptime(ore[1], "%H:%M")
            delta = timedelta(minutes=min)
            t = start
            while t <= end:
                intervallo.append(datetime.strftime(t, '%H:%M'))
                t += delta

        return intervallo

def interval_time_single2(lista_ore,min):
        intervallo=[]
        print(lista_ore)
        for ore in lista_ore:
            start = datetime.strptime(ore[0], "%H:%M")
            end = datetime.strptime(ore[1], "%H:%M")
            delta = timedelta(minutes=min)
            prev = start + delta
            print(prev)
            if(prev == end):
                intervallo.append(datetime.strftime(start, '%H:%M'))
            else:    
                t = start
                while t < end:
                    intervallo.append(datetime.strftime(t, '%H:%M'))
                    t += delta
        print(intervallo)
        return intervallo        

def day_repeat(giorno):
        intervallo=[]
        lista_ore=[]
        for ore in lista_ore:
            start = datetime.strptime(ore[0], "%H:%M")
            end = datetime.strptime(ore[1], "%H:%M")
            delta = timedelta(minutes=min)
            t = start
            while t <= end:
                intervallo.append(datetime.strftime(t, '%H:%M'))
                t += delta

        return intervallo


def proposte_giorno(mydate,docente):
    count = 1
    proposte = []
    verifica = ""
    while count<7:
        dwx = datetime.strptime(mydate, "%d-%m-%Y")
        dwx = dwx.date()
        dw =  dwx + timedelta(days=7)
        cnvdata = datetime.strptime(str(dw), "%Y-%m-%d").strftime("%d-%m-%Y")
        proposte.append(cnvdata)
        #verifica = op.getVerApp(cnvdata,docente)
        #print(verifica)
        #if verifica == 'no':
        #    proposte.append(cnvdata)

        count = count+1
        mydate = cnvdata



    return proposte

"""
@app.route('/<int:ida>/settimana_docente', methods=('GET','POST'))
def settimana_docente(ida):
    week = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    desc_mese = []
    desc_mese = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug','Ago','Set','Ott','Nov','Dic']
    miadata = date.today()
    miomese = desc_mese[miadata.month-1]
    mioanno = miadata.year

    lista_giorni = []
    intervallo = []
    proposte = []
    intervallo_tmp = []
    completo = []
    orariodoc = []
    working_hours_p1 = []
    lista_lunedi=[]
    p_giorni = []
    ore_libere = []
    ore_lavorative = []
    ore_impegnate = []
    orario_lavoro = []
    ore_doc = []
    work = []

    stampa_ora_docente =""
    msg = ""

    time_def=30

    #-- Verifico se è impostata un frazione di intervallo predefinita per docente -- #

    frazione = 30
    intervallo_doc = op.getIntervallo(ida)
    if intervallo_doc != "":
        frazione = int(intervallo_doc)

    #-- Altrimenti inserisco di defasult 30 minuti di intervallo --#



    giorno = 0
    while giorno<14:
        if giorno==0:
            oggi = date.today()
            dw = oggi - timedelta(days=oggi.weekday())
        else:
            oggi = date.today()
            inizio_settimana = oggi - timedelta(days=oggi.weekday())
            dw = inizio_settimana + timedelta(days=giorno)

        cnvdata = datetime.strptime(str(dw), "%Y-%m-%d").strftime("%d-%m-%Y")

        appuntamenti = op.getAppuntamenti(ida,dw)

        vecchio_al=""
        for cal in appuntamenti:
            app_dal = cal.dal
            app_al = cal.al
            if vecchio_al != app_dal:
                vecchio_al=cal.al
            else:
                ore_impegnate.append(app_dal)
                vecchio_al=cal.al





        ore_impegnate.sort()


        desc_day = week[dw.weekday()]
        myweek = Wk(cnvdata,desc_day)


        orario_lavoro = op.getOrarioDocente_Giorno2(ida,desc_day)

        sample_str = str(orario_lavoro)
        stampa_ora_docente = sample_str.replace("'","")

        intervallo_temp=interval_time_single(orario_lavoro,frazione)


        intervallo = [i for i in intervallo_temp if i not in ore_impegnate]
        ultimo_orario = ""
        ultimo_appuntamento = []
        prime_app = []
        jobtime = []
        sel_pr_app = []
        if len(ore_impegnate) != 0:
            u_cal = appuntamenti[-1]
            ultimo_orario = str(intervallo_temp[-1])

            if u_cal.al == ultimo_orario:
                ultimo_appuntamento.append(u_cal.al)
                intervallo = [i for i in intervallo if i not in ultimo_appuntamento]

            jobtime = op.getOrarioDocente_Giorno(ida,desc_day)

            prime_app = op.getTGAppuntamento(ida,dw)

            if prime_app:
                if jobtime:
                    for oraz in jobtime:
                        dal_z = oraz.dal

                        for indiapp in range(len(prime_app)):
                            pa = prime_app[indiapp]

                            if pa == dal_z:
                                sel_pr_app.append(pa)

                    if sel_pr_app:
                        intervallo = [i for i in intervallo if i not in sel_pr_app]






        ore_lavorative.append(intervallo)

        p_giorni=proposte_giorno(cnvdata,ida)
        proposte.append(p_giorni)


        lista_giorni.append(myweek)
        giorno = giorno+1

        ore_doc.append(stampa_ora_docente)

        stampa_ora_docente =""
        intervallo = []
        intervallo_temp = []
        ore_impegnate = []
        p_giorni = []


    clienti = op.getAllClienti()
    docente = op.getDocente(ida)

    return render_template("VisWeek.html", risposta=msg, listagio = lista_giorni, orario_docente=ore_doc, orario_libero = ore_lavorative, clienti=clienti,docente=docente,proposte=proposte )




@app.route('/<int:ida>/<myday>/next_week', methods=('GET','POST'))
def next_week(ida,myday):
    week = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    lista_giorni = []
    intervallo = []
    proposte = []
    intervallo_tmp = []
    completo = []
    orariodoc = []
    working_hours_p1 = []
    lista_lunedi=[]
    ore_libere = []
    ore_lavorative = []
    ore_impegnate = []
    orario_lavoro = []
    ore_doc = []
    work = []
    stampa_ora_docente =""
    msg = ""



    time_def=30
    #-- Verifico se è impostata un frazione di intervallo predefinita per docente -- #

    frazione = 30
    intervallo_doc = op.getIntervallo(ida)
    if intervallo_doc != "":
        frazione = int(intervallo_doc)

    #-- Altrimenti inserisco di defasult 30 minuti di intervallo --#


    dwx = datetime.strptime(myday, "%d-%m-%Y")
    dwx = dwx.date() + timedelta(days=1)

    giorno = 0
    while giorno<14:
        if giorno==0:
            dw = dwx
        else:
            dw =  dwx + timedelta(days=giorno)


        cnvdata = datetime.strptime(str(dw), "%Y-%m-%d").strftime("%d-%m-%Y")

        appuntamenti = op.getAppuntamenti(ida,dw)

        vecchio_al =""

        for cal in appuntamenti:
            app_dal = cal.dal
            app_al = cal.al
            if vecchio_al != app_dal:

                    vecchio_al=cal.al
            else:
                ore_impegnate.append(app_dal)
                vecchio_al=cal.al



        ore_impegnate.sort()


        desc_day = week[dw.weekday()]
        myweek = Wk(cnvdata,desc_day)


        orario_lavoro = op.getOrarioDocente_Giorno2(ida,desc_day)

        sample_str = str(orario_lavoro)
        stampa_ora_docente = sample_str.replace("'","")

        intervallo_temp=interval_time_single(orario_lavoro,frazione)



        intervallo = [i for i in intervallo_temp if i not in ore_impegnate]

        ultimo_orario = ""
        ultimo_appuntamento = []
        prime_app = []
        jobtime = []
        sel_pr_app = []
        if len(ore_impegnate) != 0:
            u_cal = appuntamenti[-1]
            ultimo_orario = str(intervallo_temp[-1])

            if u_cal.al == ultimo_orario:
                ultimo_appuntamento.append(u_cal.al)
                intervallo = [i for i in intervallo if i not in ultimo_appuntamento]

            jobtime = op.getOrarioDocente_Giorno(ida,desc_day)

            prime_app = op.getTGAppuntamento(ida,dw)

            if prime_app:
                if jobtime:
                    for oraz in jobtime:
                        dal_z = oraz.dal

                        for indiapp in range(len(prime_app)):
                            pa = prime_app[indiapp]

                            if pa == dal_z:
                                sel_pr_app.append(pa)

                    if sel_pr_app:
                        intervallo = [i for i in intervallo if i not in sel_pr_app]

        ore_lavorative.append(intervallo)

        p_giorni=proposte_giorno(cnvdata,ida)
        proposte.append(p_giorni)

        lista_giorni.append(myweek)
        giorno = giorno+1

        ore_doc.append(stampa_ora_docente)

        stampa_ora_docente =""
        intervallo = []
        intervallo_temp = []
        ore_impegnate = []
        p_giorni = []


    clienti = op.getAllClienti()
    docente = op.getDocente(ida)

    return render_template("VisWeek.html", risposta=msg, listagio = lista_giorni, orario_docente=ore_doc, orario_libero = ore_lavorative, clienti=clienti,docente=docente,proposte=proposte )


@app.route('/<int:ida>/<myday>/prev_week', methods=('GET','POST'))
def prev_week(ida,myday):
    week = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    lista_giorni = []
    intervallo = []
    proposte = []
    intervallo_tmp = []
    completo = []
    orariodoc = []
    working_hours_p1 = []
    lista_lunedi=[]
    ore_libere = []
    ore_lavorative = []
    ore_impegnate = []
    orario_lavoro = []
    ore_doc = []
    work = []
    stampa_ora_docente =""
    msg = ""
    revese = []


    time_def=30
    #-- Verifico se è impostata un frazione di intervallo predefinita per docente -- #

    frazione = 30
    intervallo_doc = op.getIntervallo(ida)
    if intervallo_doc != "":
        frazione = int(intervallo_doc)

    #-- Altrimenti inserisco di defasult 30 minuti di intervallo --#


    dwx = datetime.strptime(myday, "%d-%m-%Y")
    dwx = dwx.date() - timedelta(days=1)

    giorno = 0
    while giorno<14:
        if giorno==0:
            dw = dwx
            revese.append(dw)
            giorno = giorno+1
        else:
            dw =  dwx - timedelta(days=giorno)
            revese.append(dw)
            giorno = giorno+1

    revese.reverse()

    for r in range(len(revese)):
        dw = revese[r]

        cnvdata = datetime.strptime(str(dw), "%Y-%m-%d").strftime("%d-%m-%Y")

        appuntamenti = op.getAppuntamenti(ida,dw)

        vecchio_al =""

        for cal in appuntamenti:
            app_dal = cal.dal
            app_al = cal.al
            if vecchio_al != app_dal:

                    vecchio_al=cal.al
            else:
                ore_impegnate.append(app_dal)
                vecchio_al=cal.al



        ore_impegnate.sort()


        desc_day = week[dw.weekday()]
        myweek = Wk(cnvdata,desc_day)


        orario_lavoro = op.getOrarioDocente_Giorno2(ida,desc_day)

        sample_str = str(orario_lavoro)
        stampa_ora_docente = sample_str.replace("'","")

        intervallo_temp=interval_time_single(orario_lavoro,frazione)



        intervallo = [i for i in intervallo_temp if i not in ore_impegnate]

        ultimo_orario = ""
        ultimo_appuntamento = []
        prime_app = []
        jobtime = []
        sel_pr_app = []
        if len(ore_impegnate) != 0:
            u_cal = appuntamenti[-1]
            ultimo_orario = str(intervallo_temp[-1])

            if u_cal.al == ultimo_orario:
                ultimo_appuntamento.append(u_cal.al)
                intervallo = [i for i in intervallo if i not in ultimo_appuntamento]

            jobtime = op.getOrarioDocente_Giorno(ida,desc_day)

            prime_app = op.getTGAppuntamento(ida,dw)

            if prime_app:
                if jobtime:
                    for oraz in jobtime:
                        dal_z = oraz.dal

                        for indiapp in range(len(prime_app)):
                            pa = prime_app[indiapp]

                            if pa == dal_z:
                                sel_pr_app.append(pa)

                    if sel_pr_app:
                        intervallo = [i for i in intervallo if i not in sel_pr_app]

        ore_lavorative.append(intervallo)

        p_giorni=proposte_giorno(cnvdata,ida)
        proposte.append(p_giorni)

        lista_giorni.append(myweek)


        ore_doc.append(stampa_ora_docente)

        stampa_ora_docente =""
        intervallo = []
        intervallo_temp = []
        ore_impegnate = []
        p_giorni = []


    clienti = op.getAllClienti()
    docente = op.getDocente(ida)

    return render_template("VisWeek.html", risposta=msg, listagio = lista_giorni, orario_docente=ore_doc, orario_libero = ore_lavorative, clienti=clienti,docente=docente,proposte=proposte )

"""

@app.route('/<int:ida>/nuovo_appuntamento', methods=('GET','POST'))
def nuovo_appuntamento(ida):
    msg=""
    min = 30
    ore_impegnate = []
    ore_intervallo = []
    #-- Verifico se è impostata un frazione di intervallo predefinita per docente -- #

    intervallo_doc = op.getIntervallo(ida)
    if intervallo_doc != "":
        min = int(intervallo_doc)

    #-- Altrimenti inserisco di defasult 30 minuti di intervallo --#
    report=""
    studente =[]
    listapp = []
    tot_hours = 0
    tot_def=0.0
    today = date.today()
    if request.method == 'POST':
        giorno = request.form.get('DataG')
        dal = request.form.get('Dal')
        al = request.form.get('Al')
        #alunno = request.form.get('Cliente')
        alunno = request.form.getlist('Cliente')
        note = request.form.get('Note')
        idt=""
        if alunno:

            for studente in alunno:
                verifica = op.getVerApp(giorno,ida,dal,al)
                if verifica == 'si':
                    report = report+"<tr class=\"table-danger\"><td class=\"text-bold-500\">"+giorno+"</td><td>"+dal+"</td><td>"+al+"</td><td class=\"text-bold-500\"><a href=\"/"+str(ida)+"/settimana_docente\"><i class=\"ficon bx bx-bell bx-tada bx-flip-horizontal\"></i>ORARIO NON DISPONIBILE</a></td></tr>"
                else:
                    giorno_object = datetime.strptime(giorno, "%d-%m-%Y").date()
                    
                    ore_impegnate = []
                    #formatted_date_string = date_object.strftime("%Y-%m-%d")
                    appuntamenti = op.getAppuntamenti(ida,giorno_object)
                   
                    for cal in appuntamenti:
                        app_dal = cal.dal          
                        ore_impegnate.append(app_dal)
                    
                    ore_impegnate.sort()
                    
                    lista_orario=[]
                    lista_orario.append([dal,al])
                    ore_intervallo=interval_time_single2(lista_orario,min)
                   
                    if ore_impegnate and any(item in ore_impegnate for item in ore_intervallo):
                        report = report+"<tr class=\"table-danger\"><td class=\"text-bold-500\">"+giorno+"</td><td>"+dal+"</td><td>"+al+"</td><td class=\"text-bold-500\"><a href=\"/"+str(ida)+"/settimana_docente\"><i class=\"ficon bx bx-bell bx-tada bx-flip-horizontal\"></i>ORARIO NON DISPONIBILE</a></td></tr>"
                    else:
                        idt = op.getID("appuntamenti_text")
                        msg = op.nuovo_appuntamento_text(ida,giorno,dal,al,studente,note,idt)
                        report = report+"<tr class=\"table-active\"><td class=\"text-bold-500\">"+giorno+"</td><td>"+dal+"</td><td>"+al+"</td><td class=\"text-bold-500\">APPUNTAMENTO INSERITO</td></tr>"

                        selezione = request.form.getlist('Reiter')

                        start = datetime.strptime(dal, "%H:%M")
                        end = datetime.strptime(al, "%H:%M")

                        delta = timedelta(minutes=min)

                        t = start
                        while t < end:
                            id = op.getID("appuntamenti")
                            msg = op.nuovo_appuntamento(ida,giorno,datetime.strftime(t, '%H:%M'),datetime.strftime(t+delta, '%H:%M'),studente,note,id,idt)
                            t += delta

                        if selezione:

                            for sel in selezione:
                                verifica = op.getVerApp(sel,ida,dal,al)
                                if verifica == 'si':
                                    report = report+"<tr class=\"table-danger\"><td class=\"text-bold-500\">"+sel+"</td><td>"+dal+"</td><td>"+al+"</td><td class=\"text-bold-500\"><a href=\"/"+str(ida)+"/settimana_docente\"><i class=\"ficon bx bx-bell bx-tada bx-flip-horizontal\"></i>ORARIO NON DISPONIBILE</a></td></tr>"
                                else:
                                    sel_object = datetime.strptime(sel, "%d-%m-%Y").date()
                                    
                                    appuntamenti_ = op.getAppuntamenti(ida,sel_object)
                                    ore_impegnate = []
                                    for cal_ in appuntamenti_:
                                        app_dal = cal_.dal     
                                        ore_impegnate.append(app_dal)
                                        
                    
                                    ore_impegnate.sort()
                                    
                                    lista_orario=[]
                                    lista_orario.append([dal,al])
                                    ore_intervallo=interval_time_single2(lista_orario,min)
                                    if ore_impegnate and any(item in ore_impegnate for item in ore_intervallo):
                                        report = report+"<tr class=\"table-danger\"><td class=\"text-bold-500\">"+sel+"</td><td>"+dal+"</td><td>"+al+"</td><td class=\"text-bold-500\"><a href=\"/"+str(ida)+"/settimana_docente\"><i class=\"ficon bx bx-bell bx-tada bx-flip-horizontal\"></i>ORARIO NON DISPONIBILE</a></td></tr>"
                                    else:
                                        idtext = op.getID("appuntamenti_text")
                                        msg = op.nuovo_appuntamento_text(ida,sel,dal,al,studente,note,idtext)
                                        report = report+"<tr class=\"table-active\"><td class=\"text-bold-500\">"+sel+"</td><td>"+dal+"</td><td>"+al+"</td><td class=\"text-bold-500\">APPUNTAMENTO INSERITO</td></tr>"
                                        t = start
                                        if sel:
                                            while t < end:
                                                id = op.getID("appuntamenti")

                                                msg = op.nuovo_appuntamento(ida,sel,datetime.strftime(t, '%H:%M'),datetime.strftime(t+delta, '%H:%M'),studente,note,id,idtext)
                                                t += delta

                    x = len(alunno)
                    if x == 1:
                        listapp = op.getAppClienteG(alunno[0],today)
                        studente = op.getCliente(alunno[0])

        else:

            esito=""
            nomes = request.form.get('NomeS')

            cognomes = request.form.get('CognomeS')

            emails = request.form.get('EmailS')

            phones = request.form.get('TelefonoS')

            if nomes:
                Id_cliente = op.getID("cliente")
                esito = op.nuovo_cliente(nomes,cognomes,"","","",emails,"01/01/1900",phones,"",Id_cliente,date.today(),"Gestionale");
                if esito=="Inserimento avvenuto con successo":
                    verifica = op.getVerApp(giorno,ida,dal,al)
                    if verifica == 'si':
                        report = report+"<tr class=\"table-danger\"><td class=\"text-bold-500\">"+giorno+"</td><td>"+dal+"</td><td>"+al+"</td><td class=\"text-bold-500\"><a href=\"/"+str(ida)+"/settimana_docente\"><i class=\"ficon bx bx-bell bx-tada bx-flip-horizontal\"></i>ORARIO NON DISPONIBILE</a></td></tr>"
                    else:
                        giorno_object = datetime.strptime(giorno, "%d-%m-%Y").date()
                      
                        ore_impegnate = []
                        appuntamenti = op.getAppuntamenti(ida,giorno_object)
                   
                        for cal in appuntamenti:
                            app_dal = cal.dal          
                            ore_impegnate.append(app_dal)
                    
                        ore_impegnate.sort()

                        lista_orario=[]
                        lista_orario.append([dal,al])
                        ore_intervallo=interval_time_single2(lista_orario,min)
                        if ore_impegnate and any(item in ore_impegnate for item in ore_intervallo):
                            report = report+"<tr class=\"table-danger\"><td class=\"text-bold-500\">"+giorno+"</td><td>"+dal+"</td><td>"+al+"</td><td class=\"text-bold-500\"><a href=\"/"+str(ida)+"/settimana_docente\"><i class=\"ficon bx bx-bell bx-tada bx-flip-horizontal\"></i>ORARIO NON DISPONIBILE</a></td></tr>"
                        else:
                            idt = op.getID("appuntamenti_text")
                            msg = op.nuovo_appuntamento_text(ida,giorno,dal,al,Id_cliente,note,idt)
                            report = report+"<tr class=\"table-active\"><td class=\"text-bold-500\">"+giorno+"</td><td>"+dal+"</td><td>"+al+"</td><td class=\"text-bold-500\">APPUNTAMENTO INSERITO</td></tr>"

                            selezione = request.form.getlist('Reiter')

                            start = datetime.strptime(dal, "%H:%M")
                            end = datetime.strptime(al, "%H:%M")

                            delta = timedelta(minutes=min)

                            t = start
                            while t < end:
                                id = op.getID("appuntamenti")
                                msg = op.nuovo_appuntamento(ida,giorno,datetime.strftime(t, '%H:%M'),datetime.strftime(t+delta, '%H:%M'),Id_cliente,note,id,idt)
                                t += delta

                            if selezione:
                               
                                for sel in selezione:
                                
                                    verifica = op.getVerApp(sel,ida,dal,al)
                                 
                                    if verifica == 'si':
                                        report = report+"<tr class=\"table-danger\"><td class=\"text-bold-500\">"+sel+"</td><td>"+dal+"</td><td>"+al+"</td><td class=\"text-bold-500\"><a href=\"/"+str(ida)+"/settimana_docente\"><i class=\"ficon bx bx-bell bx-tada bx-flip-horizontal\"></i>ORARIO NON DISPONIBILE</a></td></tr>"
                                    else:
                                        sel_object = datetime.strptime(sel, "%d-%m-%Y").date()
                                        appuntamenti__ = op.getAppuntamenti(ida,sel_object)
                                        ore_impegnate = []
                                        for cal__ in appuntamenti__:
                                            app_dal__ = cal__.dal     
                                            ore_impegnate.append(app_dal__)
                                        
                    
                                        ore_impegnate.sort()
                             
                                        lista_orario=[]
                                        lista_orario.append([dal,al])
                                        ore_intervallo=interval_time_single2(lista_orario,min)
                                        if ore_impegnate and any(item in ore_impegnate for item in ore_intervallo):
                                            report = report+"<tr class=\"table-danger\"><td class=\"text-bold-500\">"+sel+"</td><td>"+dal+"</td><td>"+al+"</td><td class=\"text-bold-500\"><a href=\"/"+str(ida)+"/settimana_docente\"><i class=\"ficon bx bx-bell bx-tada bx-flip-horizontal\"></i>ORARIO NON DISPONIBILE</a></td></tr>"
                                        else:
                                            idtext = op.getID("appuntamenti_text")
                                            msg = op.nuovo_appuntamento_text(ida,sel,dal,al,Id_cliente,note,idtext)
                                            report = report+"<tr class=\"table-active\"><td class=\"text-bold-500\">"+sel+"</td><td>"+dal+"</td><td>"+al+"</td><td class=\"text-bold-500\">APPUNTAMENTO INSERITO</td></tr>"
                                            t = start
                                
                                        if sel:
                                            while t < end:
                                                id = op.getID("appuntamenti")
                                                msg = op.nuovo_appuntamento(ida,sel,datetime.strftime(t, '%H:%M'),datetime.strftime(t+delta, '%H:%M'),Id_cliente,note,id,idtext)
                                                t += delta


                    listapp = op.getAppClienteG(Id_cliente,today)
                    studente = op.getCliente(Id_cliente)



   #ricavo totale ore studente
    for apx in listapp:
        startx=datetime.strptime(apx.dal,"%H:%M")
        endx=datetime.strptime(apx.al,"%H:%M")
        diff = endx - startx
        diff_in_hours = diff.total_seconds() / 3600
        tot_hours = tot_hours + diff_in_hours


    return render_template("Result.html", risposta=msg, id=ida,listapp=listapp,report=report,studente=studente,totore = tot_hours )


@app.route('/<int:ida>/free_appuntamento', methods=('GET','POST'))
def free_appuntamento(ida):
    msg=""
    min = 30
    #-- Verifico se è impostata un frazione di intervallo predefinita per docente -- #

    intervallo_doc = op.getIntervallo(ida)
    if intervallo_doc != "":
        min = int(intervallo_doc)

    #-- Altrimenti inserisco di defasult 30 minuti di intervallo --#
    report=""
    studente =[]
    listapp = []
    tot_hours = 0
    tot_def=0.0
    today = date.today()
    if request.method == 'POST':
        giorno = request.form.get('DataG')
        dal = request.form.get('Dal')
        al = request.form.get('Al')
        #alunno = request.form.get('Cliente')
        alunno = request.form.getlist('Cliente')
        note = request.form.get('Note')
        idt=""
        if alunno:

            for studente in alunno:

                idt = op.getID("appuntamenti_text")
                msg = op.nuovo_appuntamento_text(ida,giorno,dal,al,studente,note,idt)
                report = report+"<tr class=\"table-active\"><td class=\"text-bold-500\">"+giorno+"</td><td>"+dal+"</td><td>"+al+"</td><td class=\"text-bold-500\">APPUNTAMENTO INSERITO</td></tr>"

                selezione = request.form.getlist('Reiter')

                start = datetime.strptime(dal, "%H:%M")
                end = datetime.strptime(al, "%H:%M")

                delta = timedelta(minutes=min)

                t = start
                while t < end:
                    id = op.getID("appuntamenti")
                    msg = op.nuovo_appuntamento(ida,giorno,datetime.strftime(t, '%H:%M'),datetime.strftime(t+delta, '%H:%M'),studente,note,id,idt)
                    t += delta

                if selezione:

                    for sel in selezione:
                        idtext = op.getID("appuntamenti_text")
                        msg = op.nuovo_appuntamento_text(ida,sel,dal,al,studente,note,idtext)
                        report = report+"<tr class=\"table-active\"><td class=\"text-bold-500\">"+sel+"</td><td>"+dal+"</td><td>"+al+"</td><td class=\"text-bold-500\">APPUNTAMENTO INSERITO</td></tr>"
                        t = start
                        if sel:
                            while t < end:
                                id = op.getID("appuntamenti")

                                msg = op.nuovo_appuntamento(ida,sel,datetime.strftime(t, '%H:%M'),datetime.strftime(t+delta, '%H:%M'),studente,note,id,idtext)
                                t += delta

            x = len(alunno)
            if x == 1:
                listapp = op.getAppClienteG(alunno[0],today)
                studente = op.getCliente(alunno[0])





   #ricavo totale ore studente
    for apx in listapp:
        startx=datetime.strptime(apx.dal,"%H:%M")
        endx=datetime.strptime(apx.al,"%H:%M")
        diff = endx - startx
        diff_in_hours = diff.total_seconds() / 3600
        tot_hours = tot_hours + diff_in_hours


    return render_template("FreeResult.html", risposta=msg, id=ida,listapp=listapp,report=report,studente=studente,totore = tot_hours )












@app.route('/<int:ida>/app_doc', methods=('GET','POST'))
def app_doc(ida):
    msg = ""
    today = date.today()
    msg = "Mese in corso"
    listapp = op.getAppDocDayG(ida,today)
    #listapp = op.getAppDocDay(ida,today)
    docente = op.getDocente(ida)
    #ragsoc  = docente.nome+" "+docente.cognome
    return render_template("AppDoc.html", listapp=listapp,risposta=msg,ragsoc=docente)

@app.route('/<int:ida>/app_doc_result', methods=('GET','POST'))
def app_doc_result(ida):

    today = date.today()
    msg = ""

    if request.method == 'POST':
        dal = request.form.get('Dal')
        al = request.form.get('Al')

        if dal=='' or al=='':
            #listapp = op.getAppDocDay(ida,today)
            listapp = op.getAppDocDayG(ida,today)
            msg = "Mese in corso"
        else:
            listapp = op.getAppDocRangeG(ida,dal,al)
            #listapp = op.getAppDocRange(ida,dal,al)
            msg = dal+" - "+al


    docente = op.getDocente(ida)
    #ragsoc  = docente.nome+" "+docente.cognome
    return render_template("AppDoc.html", listapp=listapp,risposta=msg,ragsoc=docente)

@app.route('/<int:ida>/<gs>/app_doc_direct', methods=('GET','POST'))
def app_doc_direct(ida,gs):
    today=""
    msg = ""
    gs =gs.replace("/","-")
    if gs:
        listapp = op.getAppDocRangeG(ida,gs,gs)
        msg = gs
    else:
        listapp = op.getAppDocDayG(ida,today)
        msg = "Mese in corso"

    docente = op.getDocente(ida)
    return render_template("AppDoc.html", listapp=listapp,risposta=msg,ragsoc=docente)


@app.route('/<int:ida>/<giorno>/app_doc_day', methods=('GET','POST'))
def app_doc_day(ida,giorno):
    msg = ""
    today = giorno
    listapp = op.getAppDocDayG(ida,today)
    docente = op.getDocente(ida)
    #ragsoc  = docente.nome+" "+docente.cognome
    return render_template("AppDoc.html", listapp=listapp,risposta=msg,ragsoc=docente)

@app.route('/<int:ida>/app_cli', methods=('GET','POST'))
def app_cli(ida):
    msg = ""
    today = date.today()
    listapp = op.getAppClienteG(ida,today)
    #mesecorr = op.getMeseCliente(ida)
    orec = op.getOreConteggio(ida)

    tot_hours = 0
    tot_def=0.0
    for app in listapp:
        start=datetime.strptime(app.dal,"%H:%M")
        end=datetime.strptime(app.al,"%H:%M")
        diff = end - start
        diff_in_hours = diff.total_seconds() / 3600
        tot_hours = tot_hours + diff_in_hours

    if orec:
        tot_def = int(orec)-tot_hours

    else:
        tot_def = tot_hours
        orec="0"

    cliente = op.getCliente(ida)
    ragsoc  = cliente.nome+" "+cliente.cognome
    msg="a partire da oggi"
    return render_template("AppCli.html", listapp=listapp,risposta=msg,ragsoc=cliente,tot_ore=tot_hours,orec=orec,tot_def=tot_def)


@app.route('/<int:ida>/app_cli_result', methods=('GET','POST'))
def app_cli_result(ida):

    today = date.today()
    msg = ""

    if request.method == 'POST':
        dal = request.form.get('Dal')
        al = request.form.get('Al')

        if dal=='' or al=='':
            listapp = op.getAppClienteG(ida,today)
            msg = "a partire da oggi"
        else:
            listapp = op.getAppCliRangeG(ida,dal,al)
            msg = dal+" - "+al


    orec = op.getOreConteggio(ida)

    tot_hours = 0
    tot_def=0.0
    for app in listapp:
        start=datetime.strptime(app.dal,"%H:%M")
        end=datetime.strptime(app.al,"%H:%M")
        diff = end - start
        diff_in_hours = diff.total_seconds() / 3600
        tot_hours = tot_hours + diff_in_hours

    if orec:
        tot_def = int(orec)-tot_hours

    else:
        tot_def = tot_hours
        orec="0"

    cliente = op.getCliente(ida)
    ragsoc  = cliente.nome+" "+cliente.cognome
    return render_template("AppCli.html", listapp=listapp,risposta=msg,ragsoc=cliente,tot_ore=tot_hours,orec=orec,tot_def=tot_def)





@app.route('/<int:ida>/ore_cli', methods=('GET','POST'))
def ore_cli(ida):
    msg = ""
    today = date.today()
    cliente = op.getCliente(ida)
    ragsoc  = cliente.nome+" "+cliente.cognome
    listapro = op.getConteggio(ida)
    return render_template("OreCli.html",risposta=msg,ragsoc=ragsoc,listapro=listapro,iddoc=ida)


@app.route('/<int:ida>/nuovo_conteggio', methods=('GET','POST'))
def nuovo_conteggio(ida):
    msg=""
    if request.method == 'POST':
        ore = request.form.get('Ore')
        status = request.form.get('Status')
        giorno = date.today()
        id = op.getID("conteggio")
        msg = op.nuovo_conteggio(ida,ore,status,giorno,id)


    cliente = op.getCliente(ida)
    ragsoc  = cliente.nome+" "+cliente.cognome
    listapro = op.getConteggio(ida)
    return render_template("OreCli.html",risposta=msg,ragsoc=ragsoc,listapro=listapro,iddoc=ida)


@app.route('/plan_doc', methods=('GET','POST'))
def plan_doc():
    msg = ""
    count = 0
    week = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    #today = date.today() + timedelta(days=1)
    today = date.today()
    desc_day = week[today.weekday()]
    listapp=op.getDailyPlan(today)
    dox = ""
    for app in listapp:

        if count==0:
            msg=msg+"<tr> <td><div class=\"badge badge-pill badge-light-secondary mr-1 mb-1\">"+app.id_docente+"</div></td> <td></td> <td></td> <td></td> <td></td> </tr>"
            msg=msg+"<tr> <td><div class=\"badge badge-pill badge-light-warning mr-1\">"+desc_day+" | "+app.giorno+"</div></td><td><div class=\"badge badge-light-primary text-bold-500 py-50\">"+app.dal+"</div></td> <td><div class=\"badge badge-light-danger text-bold-500 py-50\">"+app.al+"</div></td> <td><div class=\"badge badge-pill badge-light-secondary mr-1 mb-1\">"+app.cliente+"</div></td> <td>"+app.note+"</td> </tr>"
            count=count+1
            dox = app.id_docente

        elif count>0 and dox == app.id_docente:
            msg=msg+"<tr> <td><div class=\"badge badge-pill badge-light-warning mr-1\">"+desc_day+" | "+app.giorno+"</div></td><td><div class=\"badge badge-light-primary text-bold-500 py-50\">"+app.dal+"</div></td> <td><div class=\"badge badge-light-danger text-bold-500 py-50\">"+app.al+"</div></td> <td><div class=\"badge badge-pill badge-light-secondary mr-1 mb-1\">"+app.cliente+"</div></td> <td>"+app.note+"</td> </tr>"
            dox = app.id_docente
            count=count+1

        elif count>0 and dox != app.id_docente:
            msg=msg+"<tr> <td><div class=\"badge badge-pill badge-light-secondary mr-1 mb-1\">"+app.id_docente+"</div></td> <td></td> <td></td> <td></td> <td></td> </tr>"
            msg=msg+"<tr> <td><div class=\"badge badge-pill badge-light-warning mr-1\">"+desc_day+" | "+app.giorno+"</div></td><td><div class=\"badge badge-light-primary text-bold-500 py-50\">"+app.dal+"</div></td> <td><div class=\"badge badge-light-danger text-bold-500 py-50\">"+app.al+"</div></td> <td><div class=\"badge badge-pill badge-light-secondary mr-1 mb-1\">"+app.cliente+"</div></td> <td>"+app.note+"</td> </tr>"
            dox = app.id_docente
            count=count+1





    giorno = datetime.strptime(str(today), "%Y-%m-%d").strftime("%d-%m-%Y")
    return render_template("PlanDoc.html",risposta=msg,listapp=listapp,giorno=giorno)


@app.route('/plan_doc_data', methods=('GET','POST'))
def plan_doc_data():
    msg = ""
    giogio=""
    dwx = None
    week = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    if request.method == 'POST':
        today = request.form.get('DataP')
        if today:
            today = today.replace("/","-")
            giogio = today
            dwx = datetime.strptime(today, "%d-%m-%Y")
            dwx = dwx.date()
            desc_day = week[dwx.weekday()]
        else:
            today = date.today() + timedelta(days=1)
            dwx = today
            desc_day = week[dwx.weekday()]
            giogio = datetime.strptime(str(today), "%Y-%m-%d").strftime("%d-%m-%Y")


    count = 0

    listapp=op.getDailyPlan(dwx)
    dox = ""
    for app in listapp:

        if count==0:
            msg=msg+"<tr> <td><div class=\"badge badge-pill badge-light-secondary mr-1 mb-1\">"+app.id_docente+"</div></td> <td></td> <td></td> <td></td> <td></td> </tr>"
            msg=msg+"<tr> <td><div class=\"badge badge-pill badge-light-warning mr-1\">"+desc_day+" | "+app.giorno+"</div></td><td><div class=\"badge badge-light-primary text-bold-500 py-50\">"+app.dal+"</div></td> <td><div class=\"badge badge-light-danger text-bold-500 py-50\">"+app.al+"</div></td> <td><div class=\"badge badge-pill badge-light-secondary mr-1 mb-1\">"+app.cliente+"</div></td> <td>"+app.note+"</td> </tr>"
            count=count+1
            dox = app.id_docente

        elif count>0 and dox == app.id_docente:
            msg=msg+"<tr> <td><div class=\"badge badge-pill badge-light-warning mr-1\">"+desc_day+" | "+app.giorno+"</div></td><td><div class=\"badge badge-light-primary text-bold-500 py-50\">"+app.dal+"</div></td> <td><div class=\"badge badge-light-danger text-bold-500 py-50\">"+app.al+"</div></td> <td><div class=\"badge badge-pill badge-light-secondary mr-1 mb-1\">"+app.cliente+"</div></td> <td>"+app.note+"</td> </tr>"
            dox = app.id_docente
            count=count+1

        elif count>0 and dox != app.id_docente:
            msg=msg+"<tr> <td><div class=\"badge badge-pill badge-light-secondary mr-1 mb-1\">"+app.id_docente+"</div></td> <td></td> <td></td> <td></td> <td></td> </tr>"
            msg=msg+"<tr> <td><div class=\"badge badge-pill badge-light-warning mr-1\">"+desc_day+" | "+app.giorno+"</div></td><td><div class=\"badge badge-light-primary text-bold-500 py-50\">"+app.dal+"</div></td> <td><div class=\"badge badge-light-danger text-bold-500 py-50\">"+app.al+"</div></td> <td><div class=\"badge badge-pill badge-light-secondary mr-1 mb-1\">"+app.cliente+"</div></td> <td>"+app.note+"</td> </tr>"
            dox = app.id_docente
            count=count+1





    giorno = giogio
    return render_template("PlanDoc.html",risposta=msg,listapp=listapp,giorno=giorno)

@app.route('/<int:ida>/<int:id_docente>/elimina_appuntamento', methods=('GET','POST'))
def elimina_appuntamento(ida,id_docente):
    appuntamento = []
    dal = ""
    al = ""
    giorno = ""
    cliente = ""
    min = 30
    today = date.today()
    msg = ""
    msg=op.elimina_dinamico(ida,"appuntamenti","Idt")
    if msg=='Eliminazione avvenuta con successo':
        op.elimina_dinamico(ida,"appuntamenti_text","Id")


    risp = datetime.strptime(str(today), "%Y-%m-%d").strftime("%d-%m-%Y")
    msg = risp+" | "+msg
    listapp = op.getAppDocDayG(id_docente,today)
    docente = op.getDocente(id_docente)
    #ragsoc  = docente.nome+" "+docente.cognome
    return render_template("AppDoc.html", listapp=listapp,risposta=msg,ragsoc=docente)

@app.route('/<int:ida>/<int:id_docente>/add_utente', methods=('GET','POST'))
def add_utente(ida,id_docente):

    msg = ""
    listapp = op.getSingleTGAppuntamento(ida)
    docente = op.getDocente(id_docente)
    clienti = op.getAllClienti()
    for app in listapp:
        giorno = app.giorno
        today = giorno.replace("/","-")
        dwx = datetime.strptime(today, "%d-%m-%Y")
        dwx = dwx.date()
        listastu = op.getStudentiApp(dwx,app.dal,app.al,id_docente)

    proposte = proposte_giorno(giorno,id_docente)

    return render_template("AddUser.html", listapp=listapp,risposta=msg,ragsoc=docente,clienti=clienti,proposte=proposte, listastu= listastu)



@app.route('/<int:ida>/<int:id_docente>/<int:id_studente>/elimina_app', methods=('GET','POST'))
def elimina_app(ida,id_docente,id_studente):
    appuntamento = []
    dal = ""
    al = ""
    giorno = ""
    cliente = ""
    min = 30
    today = date.today()
    msg = ""

    msg=op.elimina_dinamico(ida,"appuntamenti","Idt")

    if msg=='Eliminazione avvenuta con successo':
        op.elimina_dinamico(ida,"appuntamenti_text","Id")

    listapp = op.getAppClienteG(id_studente,today)
    studente = op.getCliente(id_studente)

    tot_hours = 0
    tot_def=0.0
    #ricavo totale ore studente
    for apx in listapp:
        startx=datetime.strptime(apx.dal,"%H:%M")
        endx=datetime.strptime(apx.al,"%H:%M")
        diff = endx - startx
        diff_in_hours = diff.total_seconds() / 3600
        tot_hours = tot_hours + diff_in_hours


    return render_template("EResult.html", risposta=msg, id=id_docente,listapp=listapp,studente=studente,totore = tot_hours )

@app.route('/<int:ida>/<int:id_studente>/elimina_app_cli', methods=('GET','POST'))
def elimina_app_cli(ida,id_studente):

    msg=op.elimina_dinamico(ida,"appuntamenti","Idt")

    if msg=='Eliminazione avvenuta con successo':
        op.elimina_dinamico(ida,"appuntamenti_text","Id")

    today = date.today()
    listapp = op.getAppClienteG(id_studente,today)
    orec = op.getOreConteggio(id_studente)

    tot_hours = 0
    tot_def=0.0
    for app in listapp:
        start=datetime.strptime(app.dal,"%H:%M")
        end=datetime.strptime(app.al,"%H:%M")
        diff = end - start
        diff_in_hours = diff.total_seconds() / 3600
        tot_hours = tot_hours + diff_in_hours

    if orec:
        tot_def = int(orec)-tot_hours

    else:
        tot_def = tot_hours
        orec="0"

    cliente = op.getCliente(id_studente)
    return render_template("AppCli.html", listapp=listapp,risposta=msg,ragsoc=cliente,tot_ore=tot_hours,orec=orec,tot_def=tot_def)



@app.route('/verdisp', methods=('GET','POST'))
def verdisp():
    week = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    count = 0
    ore_impegnate = []
    ore_lavorative = []
    prox_data = []
    opzioni =""
    msg=""
    if request.method == 'POST':
        dal = request.form.get('Dal')
        giorno = request.form.get('Giorno')
        docente = request.form.get('Docente')
        dwx = datetime.strptime(giorno, "%d-%m-%Y")
        dwx = dwx.date()
        appuntamenti = op.getAppuntamenti(int(docente),dwx)
        #-- Verifico se è impostata un frazione di intervallo predefinita per docente -- #

        frazione = 30
        intervallo_doc = op.getIntervallo(int(docente))
        if intervallo_doc != "":
            frazione = int(intervallo_doc)

        #-- Altrimenti inserisco di defasult 30 minuti di intervallo --#






        vecchio_al =  ""
        for cal in appuntamenti:
            app_dal = cal.dal
            app_al = cal.al


            if vecchio_al != app_dal:
                vecchio_al=cal.al
            else:
                ore_impegnate.append(app_dal)
                vecchio_al=cal.al


        ore_impegnate.sort()

        startx=datetime.strptime(dal,"%H:%M")

        desc_day = week[dwx.weekday()]

        orario_lavoro = op.getOrarioDocente_Giorno2(int(docente),desc_day)


        intervallo_temp=interval_time_single(orario_lavoro,frazione)


        intervallo = [i for i in intervallo_temp if i not in ore_impegnate]
        ultimo_orario = ""
        ultimo_appuntamento = []
        prime_app = []
        jobtime = []
        sel_pr_app = []
        if len(ore_impegnate) != 0:
            u_cal = appuntamenti[-1]
            ultimo_orario = str(intervallo_temp[-1])

            if u_cal.al == ultimo_orario:
                ultimo_appuntamento.append(u_cal.al)
                intervallo = [i for i in intervallo if i not in ultimo_appuntamento]

            jobtime = op.getOrarioDocente_Giorno(int(docente),desc_day)

            prime_app = op.getTGAppuntamento(int(docente),dwx)

            if prime_app:
                if jobtime:
                    for oraz in jobtime:
                        dal_z = oraz.dal

                        for indiapp in range(len(prime_app)):
                            pa = prime_app[indiapp]

                            if pa == dal_z:
                                sel_pr_app.append(pa)

                    if sel_pr_app:
                        intervallo = [i for i in intervallo if i not in sel_pr_app]






        #ore_lavorative.append(intervallo)
        #print("Ore Plan")
        #print(intervallo)
        orario_inutile="";
        if intervallo:
            if startx == datetime.strptime(intervallo[-1],"%H:%M"):
                opzioni=""
            else:
                #print("Data di start: ")
                #print(startx)
                for undi in range(len(intervallo)):
                    #print("Undi")
                    #print(intervallo[undi])
                    #print("----------")
                    if startx ==  datetime.strptime(intervallo[undi],"%H:%M"):
                        orario_inutile = "beccato"
                        count = 1

                    if orario_inutile == "beccato":
                        min = frazione*count
                        delta = timedelta(minutes=min)
                        tplus = startx+delta
                        #print("Tplus")
                        #print(tplus)
                        #print("----------")


                        if tplus == datetime.strptime(intervallo[undi],"%H:%M"):

                             opzioni = opzioni+"<option>"+intervallo[undi]+"</option>"
                             count = count+1




        return opzioni


    return render_template("VisWeek2.html")


@app.route('/<int:ida>/settimana_docente', methods=('GET','POST'))
def settimana_completa(ida):
    week = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    desc_mese = []
    desc_mese = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug','Ago','Set','Ott','Nov','Dic']
    miadata = date.today()
    miomese = desc_mese[miadata.month-1]
    mioanno = miadata.year

    lista_giorni = []
    lista_appuntamenti = []
    intervallo = []
    proposte = []
    intervallo_tmp = []
    completo = []
    orariodoc = []
    working_hours_p1 = []
    lista_lunedi=[]
    p_giorni = []
    ore_libere = []
    ore_lavorative = []
    ore_impegnate = []
    orario_lavoro = []
    ore_doc = []
    work = []

    stampa_ora_docente =""
    msg = ""

    time_def=30

    #-- Verifico se è impostata un frazione di intervallo predefinita per docente -- #

    frazione = 30
    intervallo_doc = op.getIntervallo(ida)
    if intervallo_doc != "":
        frazione = int(intervallo_doc)

    #-- Altrimenti inserisco di defasult 30 minuti di intervallo --#



    giorno = 0
    while giorno<14:
        if giorno==0:
            oggi = date.today()
            dw = oggi - timedelta(days=oggi.weekday())
        else:
            oggi = date.today()
            inizio_settimana = oggi - timedelta(days=oggi.weekday())
            dw = inizio_settimana + timedelta(days=giorno)
       
        cnvdata = datetime.strptime(str(dw), "%Y-%m-%d").strftime("%d-%m-%Y")

        appuntamenti = op.getAppuntamenti(ida,dw)

        vecchio_al=""
        for cal in appuntamenti:
            app_dal = cal.dal
            app_al = cal.al
            #if vecchio_al != app_dal:
            #    vecchio_al=cal.al
            #else:
            ore_impegnate.append(app_dal)
            #vecchio_al=cal.al

        ore_impegnate.sort()


        desc_day = week[dw.weekday()]
        myweek = Wk(cnvdata,desc_day)


        orario_lavoro = op.getOrarioDocente_Giorno2(ida,desc_day)

        sample_str = str(orario_lavoro)
        stampa_ora_docente = sample_str.replace("'","")

        intervallo=interval_time_single(orario_lavoro,frazione)
        #print("Ore Lavoro")
        #print(intervallo)
        #print("Ore Impegnate")
        #print(ore_impegnate)
        #intervallo = [i for i in intervallo_temp if i not in ore_impegnate]
        #ultimo_orario = ""
        #ultimo_appuntamento = []
        #prime_app = []
        #jobtime = []
        #sel_pr_app = []
        #if len(ore_impegnate) != 0:
        #    u_cal = appuntamenti[-1]
        #    ultimo_orario = str(intervallo_temp[-1])

        #    if u_cal.al == ultimo_orario:
        #        ultimo_appuntamento.append(u_cal.al)
        #        intervallo = [i for i in intervallo if i not in ultimo_appuntamento]

        #    jobtime = op.getOrarioDocente_Giorno(ida,desc_day)

        #    prime_app = op.getTGAppuntamento(ida,dw)

        #    if prime_app:
        #        if jobtime:
        #            for oraz in jobtime:
        #                dal_z = oraz.dal

        #                for indiapp in range(len(prime_app)):
        #                    pa = prime_app[indiapp]

        #                    if pa == dal_z:
        #                        sel_pr_app.append(pa)

        #            if sel_pr_app:
        #                intervallo = [i for i in intervallo if i not in sel_pr_app]






        ore_lavorative.append(intervallo)
        lista_appuntamenti.append(ore_impegnate)

        p_giorni=proposte_giorno(cnvdata,ida)
        proposte.append(p_giorni)


        lista_giorni.append(myweek)
        giorno = giorno+1

        ore_doc.append(stampa_ora_docente)

        stampa_ora_docente =""
        intervallo = []
        intervallo_temp = []
        ore_impegnate = []
        p_giorni = []


    clienti = op.getAllClienti()
    docente = op.getDocente(ida)

    return render_template("VisWeek2.html", risposta=msg, listagio = lista_giorni, orario_docente=ore_doc, orario_libero = ore_lavorative, clienti=clienti,docente=docente,proposte=proposte,appuntamenti = lista_appuntamenti )





@app.route('/stuapp', methods=('GET','POST'))
def stuapp():

    opzioni =""
    msg=""
    if request.method == 'POST':
        dal = request.form.get('Dal')
        giorno = request.form.get('Giorno')
        docente = request.form.get('Docente')
        opzioni = op.getStuApp(giorno,docente,dal)




        return opzioni


    return render_template("VisWeek2.html")





@app.route('/<int:ida>/<myday>/next_week', methods=('GET','POST'))
def next_week2(ida,myday):
    week = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    lista_giorni = []
    lista_appuntamenti = []
    intervallo = []
    proposte = []
    intervallo_tmp = []
    completo = []
    orariodoc = []
    working_hours_p1 = []
    lista_lunedi=[]
    ore_libere = []
    ore_lavorative = []
    ore_impegnate = []
    orario_lavoro = []
    ore_doc = []
    work = []
    stampa_ora_docente =""
    msg = ""



    time_def=30
    #-- Verifico se è impostata un frazione di intervallo predefinita per docente -- #

    frazione = 30
    intervallo_doc = op.getIntervallo(ida)
    if intervallo_doc != "":
        frazione = int(intervallo_doc)

    #-- Altrimenti inserisco di defasult 30 minuti di intervallo --#


    dwx = datetime.strptime(myday, "%d-%m-%Y")
    dwx = dwx.date() + timedelta(days=1)

    giorno = 0
    while giorno<14:
        if giorno==0:
            dw = dwx
        else:
            dw =  dwx + timedelta(days=giorno)


        cnvdata = datetime.strptime(str(dw), "%Y-%m-%d").strftime("%d-%m-%Y")

        appuntamenti = op.getAppuntamenti(ida,dw)

        vecchio_al=""
        for cal in appuntamenti:
            app_dal = cal.dal
            app_al = cal.al
            ore_impegnate.append(app_dal)


        ore_impegnate.sort()


        desc_day = week[dw.weekday()]
        myweek = Wk(cnvdata,desc_day)


        orario_lavoro = op.getOrarioDocente_Giorno2(ida,desc_day)

        sample_str = str(orario_lavoro)
        stampa_ora_docente = sample_str.replace("'","")

        intervallo=interval_time_single(orario_lavoro,frazione)

        ore_lavorative.append(intervallo)
        lista_appuntamenti.append(ore_impegnate)

        p_giorni=proposte_giorno(cnvdata,ida)
        proposte.append(p_giorni)


        lista_giorni.append(myweek)
        giorno = giorno+1

        ore_doc.append(stampa_ora_docente)

        stampa_ora_docente =""
        intervallo = []
        intervallo_temp = []
        ore_impegnate = []
        p_giorni = []


    clienti = op.getAllClienti()
    docente = op.getDocente(ida)

    return render_template("VisWeek2.html", risposta=msg, listagio = lista_giorni, orario_docente=ore_doc, orario_libero = ore_lavorative, clienti=clienti,docente=docente,proposte=proposte,appuntamenti = lista_appuntamenti )



@app.route('/<int:ida>/<myday>/prev_week', methods=('GET','POST'))
def prev_week2(ida,myday):
    week = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    lista_giorni = []
    lista_appuntamenti = []
    intervallo = []
    proposte = []
    intervallo_tmp = []
    completo = []
    orariodoc = []
    working_hours_p1 = []
    lista_lunedi=[]
    ore_libere = []
    ore_lavorative = []
    ore_impegnate = []
    orario_lavoro = []
    ore_doc = []
    work = []
    stampa_ora_docente =""
    msg = ""
    revese = []


    time_def=30
    #-- Verifico se è impostata un frazione di intervallo predefinita per docente -- #

    frazione = 30
    intervallo_doc = op.getIntervallo(ida)
    if intervallo_doc != "":
        frazione = int(intervallo_doc)

    #-- Altrimenti inserisco di defasult 30 minuti di intervallo --#


    dwx = datetime.strptime(myday, "%d-%m-%Y")
    dwx = dwx.date() - timedelta(days=1)

    giorno = 0
    while giorno<14:
        if giorno==0:
            dw = dwx
            revese.append(dw)
            giorno = giorno+1
        else:
            dw =  dwx - timedelta(days=giorno)
            revese.append(dw)
            giorno = giorno+1

    revese.reverse()

    for r in range(len(revese)):
        dw = revese[r]

        cnvdata = datetime.strptime(str(dw), "%Y-%m-%d").strftime("%d-%m-%Y")

        appuntamenti = op.getAppuntamenti(ida,dw)

        vecchio_al =""

        for cal in appuntamenti:
            app_dal = cal.dal
            app_al = cal.al
            ore_impegnate.append(app_dal)


        ore_impegnate.sort()


        desc_day = week[dw.weekday()]
        myweek = Wk(cnvdata,desc_day)


        orario_lavoro = op.getOrarioDocente_Giorno2(ida,desc_day)

        sample_str = str(orario_lavoro)
        stampa_ora_docente = sample_str.replace("'","")

        intervallo=interval_time_single(orario_lavoro,frazione)

        ore_lavorative.append(intervallo)
        lista_appuntamenti.append(ore_impegnate)

        p_giorni=proposte_giorno(cnvdata,ida)
        proposte.append(p_giorni)


        lista_giorni.append(myweek)
        giorno = giorno+1

        ore_doc.append(stampa_ora_docente)

        stampa_ora_docente =""
        intervallo = []
        intervallo_temp = []
        ore_impegnate = []
        p_giorni = []


    clienti = op.getAllClienti()
    docente = op.getDocente(ida)

    return render_template("VisWeek2.html", risposta=msg, listagio = lista_giorni, orario_docente=ore_doc, orario_libero = ore_lavorative, clienti=clienti,docente=docente,proposte=proposte,appuntamenti = lista_appuntamenti )
