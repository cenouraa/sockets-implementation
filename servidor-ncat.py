import socket
from threading import Thread

class Servidor:
    Clientes = []

    def __init__(self, HOST, PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # ipv4 tcp
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.socket.bind((HOST, PORT)) #0.0.0.0 7654
        self.socket.listen()
        self.socket.settimeout(600)
        self.executando = True
        print('Servidor esperando por conexão...')

    def listen(self):
        # thread para encerrar o servidor
        Thread(target=self.aguarda_encerramento, daemon=True).start()

        while self.executando:
            try:
                cliente_socket, endereco = self.socket.accept() #aceita nova conexão
            except socket.timeout:
                print('Encerrando o servidor por inatividade...')
                self.executando = False
                self.socket.close()
                for cliente in Servidor.Clientes:
                    cliente['cliente_socket'].close()
                Servidor.Clientes.clear()
                print('Servidor encerrado!')
                break
            except OSError:
                break

            print(f'Conexão de: {endereco}')

            # loop para inserir o nome
            cliente_nome = ''
            while not cliente_nome:
                try:
                    cliente_socket.send('Insira seu nome: '.encode())
                    nome = cliente_socket.recv(1024).decode()
                    if not nome: # desconectou antes de inserir o nome
                        print(f"Conexão com cliente em {endereco} foi fechada.")
                        cliente_socket.close()
                        break
                    cliente_nome = nome.strip()
                    if not cliente_nome:
                        cliente_socket.send("Voce deve inserir um nome! Tente novamente.\n".encode())

                except (ConnectionResetError, BrokenPipeError):
                    print(f"Conexão com cliente em {endereco} foi perdida.")
                    cliente_socket.close()
                    break

            if not cliente_nome:
                continue
            
            cliente_socket.send(f"Bem-vindo ao chat, {cliente_nome}!\n".encode())
            cliente = {'cliente_nome': cliente_nome, 'cliente_socket': cliente_socket}

            # faz broadcast da mensagem de entrada do novo cliente
            self.broadcast_mensagem(cliente_socket, f'{cliente_nome} entrou no chat!\n')

            Servidor.Clientes.append(cliente)

            # inicia a thread nova do cliente novo
            Thread(target=self.novo_cliente, args=(cliente,)).start()

    def aguarda_encerramento(self):
        while self.executando:
            comando = input("")
            if comando.strip().lower() == "sair":
                print('Encerrando o servidor...')
                self.executando = False
                self.socket.close()
                
                for cliente in Servidor.Clientes:
                    cliente['cliente_socket'].close()
                Servidor.Clientes.clear()
                break

    def novo_cliente(self, cliente):
        cliente_nome = cliente['cliente_nome']
        cliente_socket = cliente['cliente_socket']
        conectado = True
        while conectado:
            try:
                # fica wait esperando mensagens novas dos clientes
                cliente_mensagem = cliente_socket.recv(1024).decode()
            except:
                break
            # se não tiver mensagem, a conexão foi fechada
            if not cliente_mensagem:
                break

            # 'sair' para fechar o chat
            if cliente_mensagem.lower().strip() == "sair":
                self.broadcast_mensagem(cliente_socket, f'{cliente_nome} saiu do chat!\n')
                if cliente in Servidor.Clientes:
                    Servidor.Clientes.remove(cliente)
                cliente_socket.close()
                conectado = False
            else:
                mensagem_formatada = f'{cliente_nome}: {cliente_mensagem}\n'
                # faz broadcast da mensagem para outros clientes
                self.broadcast_mensagem(cliente_socket, mensagem_formatada)

    def broadcast_mensagem(self, remetente_socket, mensagem):
        for cliente in self.Clientes[:]:
            try:
                cliente_socket = cliente['cliente_socket']
                # nao envia para o cliente remetente
                if cliente_socket != remetente_socket:
                    cliente_socket.send(mensagem.encode())
            except:
                # se houver algum erro de conexão
                Servidor.Clientes.remove(cliente)

if __name__ == '__main__':
    servidor = Servidor('0.0.0.0', 7654)
    servidor.listen()