#BIBLIOTECAS
import socket, threading
#INFORMAÇÕES DO SERVIDOR
ip_servidor = '127.0.0.1'
porta = 7777
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.connect((ip_servidor, porta))
#VARIÁVEL GLOBAL QUE VERIFICA SE EU DEVO DESLOGAR E FECHAR O PROGRAMA
logado = {"STATUS": True}
#MENU COM AS OPÇÕES
def menu():
    print("\h : Histórico de mensagens;")
    print("\l : Lista de usuários logados;")
    print("\s : Envia uma mensagem.")
    print("\d : data e hora do servidor;")
    print("\m : envia um arquivo.")
    print("\q : desconecta do servidor;")
    
#FUNÇÃO THREAD PARA FICAR REQUISITANDO AO SERVIDOR
def enviar():
    while True:
        #se não tiver logado pare
        if logado['STATUS'] == False:
            break
        #se tiver logado, simbora
        if logado['STATUS'] == True:
            opc = input("Opção: ")
            #envia os dados no padrão, porém focando nos requisitos de uma mensagem
            if opc == '\s':
                #envio o tipo da requisição
                #padrão sempre é tamanho em bytes + dados da mensagem em bytes
                tipo = opc.encode('utf-8')
                tamanho = (len(tipo)).to_bytes(8, byteorder="little", signed=False)
                server.sendall(tamanho + tipo)
                #envia o ip destino no padrão dos bytes
                destino = input("Digite o ip destino: ").encode('utf-8')
                tamanho = (len(destino)).to_bytes(8, byteorder="little", signed=False)
                server.sendall(tamanho + destino)
                #envia a mensagem no padrão dos bytes
                msg = input("Digite sua mensagem: ").encode('utf-8')
                tamanho = (len(msg)).to_bytes(8, byteorder="little", signed=False)
                server.sendall(tamanho+msg)
            #envia uma solicitação do tipo histórico de mensagens
            #envia no padrão tamanho da mensagem + mensagem, claro que em bytes
            elif opc == '\h':
                tipo = opc.encode('utf-8')
                tamanho = (len(tipo)).to_bytes(8, byteorder="little", signed=False)
                server.sendall(tamanho + tipo)
            #envia um pedido para listar os usuários, mesmo padrão de cima
            elif opc == '\l':
                tipo = opc.encode('utf-8')
                tamanho = (len(tipo)).to_bytes(8, byteorder="little", signed=False)
                server.sendall(tamanho + tipo)
            #envia um pedido para data e hora, mesmo padrão de cima
            elif opc == '\d':
                tipo = opc.encode('utf-8')
                tamanho = (len(tipo)).to_bytes(8, byteorder="little", signed=False)
                server.sendall(tamanho + tipo)
            #envia um pedido para arquivo, no padrão de cima
            elif opc == '\m':
                #pega o nome
                nome = input("Digite o nome do arquivo: ")
                infos = b''#vai ser usado para criar um buffer
                nome_b = nome.encode('utf-8')#converte o nome
                #abre o arquivo para enviar, ele lê em bytes e envia depois os dados
                with open(nome, 'rb') as aqv:
                    while True:
                        dados = aqv.read(2000)
                        if dados == b'':#se não econtrar mais nem um byte é porque leu tudo
                            break
                        infos = infos + dados#vai motando o buffer
                #envia o tipo da mensagem no padrãozin
                tipo = opc.encode('utf-8')
                tamanho = (len(tipo)).to_bytes(8, byteorder="little", signed=False)
                server.sendall(tamanho + tipo)
                #envia o ip destino no padrão
                destino = input("Digite o ip destino: ").encode('utf-8')
                tamanho = (len(destino)).to_bytes(8, byteorder="little", signed=False)
                server.sendall(tamanho + destino)
                #envia o nome e tamanho do arquivo no padrão
                tamanho = (len(nome_b)).to_bytes(8, byteorder="little", signed=False)
                server.sendall(tamanho + nome_b)
                #envia os dados do arquivo e o seu tamanho
                tamanho = (len(infos)).to_bytes(8, byteorder="little", signed=False)
                server.sendall(tamanho + infos)

            #envia uma requisição do tipo logoff
            elif opc == '\q':
                tipo = opc.encode('utf-8')
                tamanho = (len(tipo)).to_bytes(8, byteorder="little", signed=False)
                server.sendall(tamanho + tipo)
            elif opc == '\?':#menu
                menu()   
#FUNÇÃO THREAD PARA FICAR OUVINDO O SERVIDOR
def receber():
    while True:
        #lê o tamanho da mensagem do servidor
        tamanho = int.from_bytes(server.recv(8), byteorder='little', signed=False)
        msg = server.recv(tamanho).decode('utf-8')
        #verifica o conteúdo
        #se não for um arquivo mostre os dados
        if msg != "\m":
            print("\n"+msg)
        #se for de usuário inválido, encerre e mate as threads
        if msg == "Login inválido.":
            logado['STATUS'] = False
            print("O sistema será desconectado ....")
            print("Desconsidere a proxima solicitação ...")
            break
        #se for deslogado, mate as threads
        elif msg == "Deslogado.":
            logado['STATUS'] = False
            print("O sistema será desconectado ....")
            print("Desconsidere a proxima solicitação ...")
            break
        #se for arquivo, se prepare para ler ele
        elif msg == "\m":
            #pega o nome e o tamanho do nome em bytes e converte eles
            tamanho = int.from_bytes(server.recv(8), byteorder='little', signed=False)
            nome = server.recv(tamanho).decode('utf-8')
            #pega o tamanho dos bytes do arquivo, no caso, o tamanho dele
            tamanho = int.from_bytes(server.recv(8), byteorder='little', signed=False)
            #dados = server.recv(tamanho)
            #seta para não dar erro com o tamanho atual
            t = tamanho
            #vou lendo parte por parte das mensagens do servidor e vou montando o arquivo
            #faço isso para não lotar a memória
            #lê o arquivo em bytes
            with open(nome, 'wb') as aqv:
                while t > 0:#vai lendo até ler todos os bytes, ou não tiver mais nem um dado
                    dados = server.recv(1200)
                    if dados == b'':
                        break
                    aqv.write(dados)#escrve os dados
                    t = t - 1200

#cria duas threads paralelas para ficar ouvindo e requisitando
t1 = threading.Thread(target= receber)
t2 = threading.Thread(target= enviar)
#envia a mensagem de login para poder operar no servidor
login = input("Digite seu login: ").encode('utf-8')
tamanho = (len(login)).to_bytes(8, byteorder="little", signed=False)

server.sendall(tamanho+login)

senha = input("Digite sua senha: ").encode('utf-8')
tamanho = (len(senha)).to_bytes(8, byteorder="little", signed=False)

server.sendall(tamanho+senha)
#inicializa as threads em paralelo, um para ouvir e outra para requisitar
t1.start()
t2.start()