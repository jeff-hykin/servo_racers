import traitlets
import traitlets
from adafruit_servokit import ServoKit

def get_available_i2c_ports():
    import os
    import subprocess
    import re
    def run_subcommand(*args):
        p = subprocess.Popen(['i2cdetect', *args], stdout=subprocess.PIPE,)
        values = []
        for i in range(0,9):
            line = str(p.stdout.readline())
            for match in re.finditer("[0-9][0-9]:.*[0-9][0-9]", line):
                addresses = line.split(' ')
                for possible_hex in addresses:
                    if re.match("^\d\d$", possible_hex):
                        hex_string = possible_hex
                        hex_number = int(hex_string, 16)
                        values.append(hex_number)
        return values
    return run_subcommand('-y', '-r', '1') + run_subcommand('-y', '-r', '2')

class Racecar(traitlets.HasTraits):
    steering = traitlets.Float()
    throttle = traitlets.Float()
    
    @traitlets.validate('steering')
    def _clip_steering(self, proposal):
        if proposal['value'] > 1.0:
            return 1.0
        elif proposal['value'] < -1.0:
            return -1.0
        else:
            return proposal['value']
        
    @traitlets.validate('throttle')
    def _clip_throttle(self, proposal):
        if proposal['value'] > 1.0:
            return 1.0
        elif proposal['value'] < -1.0:
            return -1.0
        else:
            return proposal['value']

class NvidiaRacecar(Racecar):
    
    i2c_address = traitlets.Integer(default_value=0x40)
    steering_gain = traitlets.Float(default_value=-0.65)
    steering_offset = traitlets.Float(default_value=0)
    steering_channel = traitlets.Integer(default_value=0)
    throttle_gain = traitlets.Float(default_value=0.8)
    throttle_channel = traitlets.Integer(default_value=1)
    
    def __init__(self, *args, **kwargs):
        super(NvidiaRacecar, self).__init__(*args, **kwargs)
        self.kit = ServoKit(channels=16, address=self.i2c_address)
        self.steering_motor = self.kit.continuous_servo[self.steering_channel]
        self.throttle_motor = self.kit.continuous_servo[self.throttle_channel]
    
    @traitlets.observe('steering')
    def _on_steering(self, change):
        self.steering_motor.throttle = change['new'] * self.steering_gain + self.steering_offset
    
    @traitlets.observe('throttle')
    def _on_throttle(self, change):
        self.throttle_motor.throttle = change['new'] * self.throttle_gain

# if __name__ == '__main__':
    car = NvidiaRacecar()
    car.run_port_test()

    # examples
    car.steering = 0.1
    car.throttle = 0.1
