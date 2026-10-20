"""Video call signaling state helper; does not capture or stream camera video."""
class VideoCall:
    def __init__(self):
        self.active=False; self.caller=None; self.receiver=None
    def request(self,caller,receiver):
        if self.active: return False
        self.caller,self.receiver,self.active=caller,receiver,True
        return True
    def respond(self,accepted):
        if not self.active: return False
        if not accepted: self.active=False
        return accepted
    def end(self):
        was_active=self.active; self.active=False
        return was_active
