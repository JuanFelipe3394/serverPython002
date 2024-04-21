#BIBLIOTECAS
from datetime import datetime
import sqlite3, socket, threading
#CRIAÇÃO DO BANCO
#------------------------------------------------------
#CRIA UM BANCO, FAÇO ELE ACEITAR MULTIPLAS THREADS, QUE SERÃO OS CLIENTES
banco = sqlite3.connect('usuarios.db', check_same_thread=False)
cursor = banco.cursor()
#CRIAÇÃO DAS TABELAS
cursor.execute("CREATE TABLE IF NOT EXISTS usuario (login text, senha text)")
cursor.execute("CREATE TABLE IF NOT EXISTS mensagem (data text, ip_o text, login_o text, ip_d text, login_d text, msg text)")
#POVOAMENTO DO BANCO COM OS USUÁRIOS
cursor.execute("INSERT INTO usuario VALUES('elohim', 'abc123')")
cursor.execute("INSERT INTO usuario VAlUES('fulano', 'abc123')")
cursor.execute("INSERT INTO usuario VALUES('ciclano', 'abc123')")
banco.commit()
#------------------------------------------------------

#SERVIDOR TCP
#------------------------------------------------------
#FICA ESCUTANDO NA PORTA E ENDEREÇO ESPECÍFICADOS
meu_ip = '127.0.0.1'#IP DA INTERFACE DO SERVIDOR
porta = 7777#PORTA DO SERVIDOR
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#SOCKET COM A CONEXÃO TCP
server.bind((meu_ip, porta))#MANDO ELE FICAR ATENDENDO NESSA PORTA/IP
server.listen()#ESCUTE
#VARIÁVEIS GLOBAIS, COM AS QUAIS EU POSSO MUDAR OS DADOS
logados = []#armazena os logins
ips = []#armazena dos ips
conexoes = []#armazena uma conexão
#------------------------------------------------------

#FUNÇÕES E OPERAÇÕES
#------------------------------------------------------
#RESPONSÁVEL POR VERIFICAR O LOGIN E LISTAR AS INFORMAÇÕES DA CONEXÃO
def logar(login, senha, con, ip):
    #VERIFICO SE USUÁRIO E SENHA EXISTEM NO BANCO
    cursor.execute("SELECT * FROM usuario WHERE login =? AND senha =?", (login, senha,))
    #PEGO A LISTA RESULTANDO COM AS TUPLAS DO BANCO
    logado = cursor.fetchall()
    #MOSTRO QUE LOGOU
    print(logado)
    #SE A LISTA TIVER TAMANHO MENOR QUE 1 É PORQUE TÁ VAZIA
    if len(logado) < 1:
        #digo que o login é inválido, retorno falso para login efetivado
        print("Login inválido.")
        return False
    else:
        #se não for menor que 1, alguém logou
        #adiciono a primeira posição da lista, pegando a 1 posição da tupla
        #essa posição representa o nome do usuário ou login
        logados.append(logado[0][0])
        #salvo a conexão do usuário
        conexoes.append(con)
        #salvo o ip daquele usuário
        ips.append(str(ip))
        #retorno a confirmação
        return True
#aqui eu digo se foi bem sucedida ou não a operação de login
def confirmar(login, senha, con, ip):
    #mando o cara logar
    status = logar(login, senha, con, ip)
    #se deu certo, avise o cara
    if status == True:
        msg = "Digite \? para ajuda.\n".encode('utf-8')#transformo em bytes
        tamanho = (len(msg)).to_bytes(8, byteorder="little", signed=False)#tamanho da mensagem
        con.sendall(tamanho+msg)#envio primeiro o tamanho e depois o conteúdo
        #retorno verdadeiro
        return True
    else:
        #se não der certo o login, eu aviso ao usuário e retorno falso
        msg = "Login inválido.".encode('utf-8')#converto em bytes
        tamanho = (len(msg)).to_bytes(8, byteorder="little", signed=False)#pego o tamnho e coberto em bytes
        con.sendall(tamanho+msg)#envio primeiro o tamanho e depois a mensagem
        return False#retorno falso
#AQUI É A THREAD QUE FICARÁ RESPONSÁVEL POR ATENDER UM USUÁRIO ESPECÍFICO
#ELA FICARÁ ATENDENDO AS REQUISIÇÕES ATÉ ELE DESLOGAR
#POR ISSO O WHILE TRUE
def opc(con):
    while True:
        #recebo o tipo da requisição do usuário
        tamanho = int.from_bytes(con.recv(8), byteorder='little', signed=False)#pego o tamanho e converto para inteiro
        msg = con.recv(tamanho).decode('utf-8')#pego a mensagem e a converto utilizando o tamanho como base

        if msg == '\s':#ele requer uma mensagem
            #pego o tamanho do ip em bytes e converto para inteiro
            tamanho = int.from_bytes(con.recv(8), byteorder='little', signed=False)
            #pego o ip e converto ele em uma string
            destino = con.recv(tamanho).decode('utf-8')
            #se ele não tiver na lista ou não for broadcast
            if destino not in ips and destino != '0.0.0.0':
                msg = "IP inexistente.".encode('utf-8')#envio o erro
                tam = (len(msg)).to_bytes(8, byteorder="little", signed=False)#pego o tamanho em bytes
                con.sendall(tam+msg)#envio o tamanho e a mensagem
            else:#se existir ou for broadcast
                tam_b = con.recv(8)#recebe o tamanho da requisição
                tamanho = int.from_bytes(tam_b, byteorder='little', signed=False)#converte para inteiro
                msg = con.recv(tamanho)#recebe a mensagem por inteira

                if destino == '0.0.0.0':#se for broadtcast
                    cursor.execute("INSERT INTO mensagem (data, ip_o, login_o, ip_d, login_d, msg) VALUES(?,?,?,?,?,?)", ((str(datetime.now())), ips[conexoes.index(con)], logados[conexoes.index(con)], destino, "Todos", msg.decode('utf-8')))
                    #insere todos os dados no banco, seguindo a ordem dos tipos
                else:#se não for broadcast
                    cursor.execute("INSERT INTO mensagem (data, ip_o, login_o, ip_d, login_d, msg) VALUES(?,?,?,?,?,?)", ((str(datetime.now())), ips[conexoes.index(con)], logados[conexoes.index(con)], destino, logados[ips.index(destino)], msg.decode('utf-8')))
                    #insere os dados de um usuário específico a partir do index comum
        elif msg == '\h':#se for historico
            cursor.execute("SELECT * FROM mensagem")#pega todas as mensagens do banco
            historico = cursor.fetchall()#pega a lista do banco
            dados = ""#variavel para controlar a formatação da mensagem mais abaixo
            
            if len(historico) < 1:#se retornar menos que um é porque não tem nada no banco
                dados = "Sem mensagens no servidor."#envia o aviso
                msg = dados.encode('utf-8')#converte os dados em bytes
                tamanho = (len(msg)).to_bytes(8, byteorder="little", signed=False)#converte o tamanho em bytes
                con.sendall(tamanho+msg)#envia o tamanho e a mensagem
            
            else:#envia as mensagens para o usuário
                #percorre a lista de tuplas retornadas pelo banco
                for mensagem in historico:
                    #lista elas de um jeito mais bonito
                    dados = dados+"\nDATA: " + mensagem[0]
                    dados = dados+"\nIP ORIGEM: " + mensagem[1]
                    dados = dados+" LOGIN ORIGEM: " + mensagem[2]
                    dados = dados+"\nIP DESTINO: " + mensagem[3]
                    dados = dados+" LOGIN DESTINO: " + mensagem[4]
                    dados = dados+"\nMENSAGEM: " + mensagem[5]
                    dados = dados+"\n"
                #converte os dados
                msg = dados.encode('utf-8')
                tamanho = (len(msg)).to_bytes(8, byteorder="little", signed=False)#pega o tamanho e converte em bytes
                con.sendall(tamanho+msg)#envia o tamanho e a mensagem
        
        elif msg == '\l':#lista todos os logins
            dados = ""#isso é para formatar abaixo mais bonito
            contador = 0#para ir pegando as informações paralelas de acordo com o index
            for logado in ips:#percorre os ips, a lista
                dados = dados + "\nIP: " + logado#formata
                dados = dados + " LOGIN: " + logados[contador]#pego o nome
                contador = contador + 1#seta para os proximos index
            #envio os dados no padrão tamanho em bytes e mensagem em bytes
            msg = dados.encode('utf-8')
            tamanho = (len(msg)).to_bytes(8, byteorder="little", signed=False)
            con.sendall(tamanho+msg)
        
        elif msg == "\d":#envio a data e a hora do servidor
            dados = "\nDATA-HORA: " + str(datetime.now())
            msg = dados.encode('utf-8')
            tamanho = (len(msg)).to_bytes(8, byteorder="little", signed=False)
            con.sendall(tamanho+msg)#envio no padrão tamanho em bytes e mensagem em bytes
        
        elif msg == "\q":#desloga um usuário
            ips.pop(conexoes.index(con))#remove o ip baseado no index da conexão
            logados.pop(conexoes.index(con))#remove o login
            conexoes.remove(con)#remove a conexão
            #envio dos dados no padrão tamnho em bytes e mensagem em bytes
            msg = "Deslogado.".encode('utf-8')
            tamanho = (len(msg)).to_bytes(8, byteorder="little", signed=False)
            con.sendall(tamanho+msg)
            con.close()#fecho a conexão
            break#mato a thread

        elif msg == "\m":#envia um arquivo
            #recebe o tamanho em bytes, e as informações em bytes, depois converte
            tamanho = int.from_bytes(con.recv(8), byteorder='little', signed=False)
            destino = con.recv(tamanho).decode('utf-8')
            #se não for broadcast ou ip conhecido
            if destino not in ips and destino != '0.0.0.0':
                #envia o aviso no padrão dos bytes
                msg = "IP inexistente.".encode('utf-8')
                tam = (len(msg)).to_bytes(8, byteorder="little", signed=False)
                con.sendall(tam+msg)
            else:#se existir, eu pego os dados
                tam_b = con.recv(8)
                #nome e tamanho do nome convertidos
                tamanho = int.from_bytes(tam_b, byteorder='little', signed=False)
                nome = con.recv(tamanho).decode('utf-8')
                #tamanho do arquivo em bytes
                tamanho = int.from_bytes(con.recv(8), byteorder='little', signed=False)
                #apenas para o controle
                t = tamanho

                dados = b''#crio um buffer com os dados do arquivo
                #abre o arquivo e fica recebendo os bytes e juntando ao buffer enquanto for maior que zero ou que não seja vazio
                with open(nome, 'wb') as aqv:
                    while t > 0:
                        dado = con.recv(1200)
                        if dado == b'':
                            break
                        dados = dados + dado
                        aqv.write(dado)
                        t = t - 1200
                #se for broadcast, envia para todos o arquivo
                if destino == '0.0.0.0':
                    #insere no banco as informações
                    cursor.execute("INSERT INTO mensagem (data, ip_o, login_o, ip_d, login_d, msg) VALUES(?,?,?,?,?,?)", ((str(datetime.now())), ips[conexoes.index(con)], logados[conexoes.index(con)], destino, "Todos", nome))
                    #formata as informações para ir enviando para todos usuários
                    nome_b = nome.encode('utf-8')
                    tam_b = len(nome_b).to_bytes(8, byteorder="little", signed=False)
                    #envia mensagem dizendo que é um arquivo
                    msg_b = '\m'.encode('utf-8')
                    tam_m = len(msg_b).to_bytes(8, byteorder="little", signed=False)
                    #vai enviando de acordo com todas conexões do servidor
                    for conexao in conexoes:
                        conexao.sendall(tam_m + msg_b)
                        conexao.sendall(tam_b + nome_b)
                        conexao.sendall((tamanho).to_bytes(8, byteorder="little", signed=False) + dados)
                    
                else:#um ip específico
                    cursor.execute("INSERT INTO mensagem (data, ip_o, login_o, ip_d, login_d, msg) VALUES(?,?,?,?,?,?)", ((str(datetime.now())), ips[conexoes.index(con)], logados[conexoes.index(con)], destino, logados[ips.index(destino)], nome))
                    #salva as informações como na mensagem
                    #envia uma mensagem dizendo que é um arquivo
                    msg_b = '\m'.encode('utf-8')
                    tam_m = len(msg_b).to_bytes(8, byteorder="little", signed=False)
                    #converte as informações
                    nome_b = nome.encode('utf-8')
                    tam_b = len(nome_b).to_bytes(8, byteorder="little", signed=False)
                    #envia os dados, no padrão tamanho em bytes e mensagem em bytes
                    conexao = conexoes[ips.index(destino)]
                    conexao.sendall(tam_m + msg_b)
                    conexao.sendall(tam_b + nome_b)
                    conexao.sendall((tamanho).to_bytes(8, byteorder="little", signed=False) + dados)
            
#enquanto for verdade va aceitando conexões
#verifique as conexões, se não for usuário deslogue
#se for, crie uma thread
while True:
    #espera uma conexão
    print("Aguardando conexões...")
    con, add = server.accept()
    print(add)
    #pega as informações do login em bytes e converte elas
    tamanho = int.from_bytes(con.recv(8), byteorder='little', signed=False)
    login = con.recv(tamanho).decode('utf-8')
    tamanho = int.from_bytes(con.recv(8), byteorder='little', signed=False)
    senha = con.recv(tamanho).decode('utf-8')
    #testa se elas são validas
    usuario = confirmar(login, senha, con, add[0])
    #se não forem, fecha a conexão
    if usuario == False:
        con.close()
    #se forem, crie uma thread para ficar atendendo o usuário
    else:
        #cria a thread e abaixo inicia ela, eu aviso que é a função opc e que ela requer uma conexão
        t = threading.Thread(target= opc, args=(con,))
        t.start()
#------------------------------------------------------