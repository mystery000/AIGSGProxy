class TCPConnectionHandler:
    def on_new_connection(
        self,
        id: str,
        remote_host: str,
        remote_port: int
    ):
        pass

    def on_data_received(
        self,
        id: str,
        data: bytes
    ):
        pass

    def on_closed(self, id: str):
        pass

    def on_sent(self, id: str, num_bytes: int):
        pass
