"""Serve on explicit loopback/private interface sockets; never all interfaces by default."""
import argparse
import socket
import uvicorn

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--host',action='append',default=[])
    p.add_argument('--port',type=int,default=18710)
    args=p.parse_args()
    if not 10000 <= args.port <= 19999:p.error('Lab policy requires a port between 10000 and 19999')
    sockets=[]
    try:
        for host in args.host or ['127.0.0.1']:
            sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            sock.bind((host,args.port));sock.listen(128);sockets.append(sock)
        server=uvicorn.Server(uvicorn.Config('monitor.backend.app:app',access_log=False,timeout_graceful_shutdown=3))
        server.run(sockets=sockets)
    finally:
        for sock in sockets:sock.close()

if __name__=='__main__':main()
