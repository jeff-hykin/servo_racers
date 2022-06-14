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
    
    i2c_address1 = traitlets.Integer(default_value=0x40)
    i2c_address2 = traitlets.Integer(default_value=0x42) #i2c_address2 = traitlets.Integer(default_value=0x60)
    steering_gain = traitlets.Float(default_value=-0.65)
    steering_offset = traitlets.Float(default_value=0)
    steering_channel = traitlets.Integer(default_value=0)
    throttle_gain = traitlets.Float(default_value=0.8)
    
    def __init__(self, *args, **kwargs):
        super(NvidiaRacecar, self).__init__(*args, **kwargs)
        # steer
        self.kit = ServoKit(channels=16, address=self.i2c_address1)
        self.steering_motor = self.kit.continuous_servo[self.steering_channel]
        
        # throttle
        self.motor = ServoKit(channels=16, address=self.i2c_address2)
    
    @traitlets.observe('steering')
    def _on_steering(self, change):
        self.steering_motor.throttle = change['new'] * self.steering_gain + self.steering_offset
    
    @traitlets.observe('throttle')
    def _on_throttle(self, change):
        if change['new'] > 0:
            self.motor._pca.channels[0].duty_cycle = int(0xFFFF * (change['new'] * self.throttle_gain))
            self.motor._pca.channels[1].duty_cycle = 0xFFFF
            self.motor._pca.channels[2].duty_cycle = 0
            self.motor._pca.channels[3].duty_cycle = 0
            self.motor._pca.channels[4].duty_cycle = int(0xFFFF * (change['new'] * self.throttle_gain))
            self.motor._pca.channels[7].duty_cycle = int(0xFFFF * (change['new'] * self.throttle_gain))
            self.motor._pca.channels[6].duty_cycle = 0xFFFF
            self.motor._pca.channels[5].duty_cycle = 0
        else:
            self.motor._pca.channels[0].duty_cycle = int(-0xFFFF * (change['new'] * self.throttle_gain))
            self.motor._pca.channels[1].duty_cycle = 0
            self.motor._pca.channels[2].duty_cycle = 0xFFFF
            self.motor._pca.channels[3].duty_cycle = int(-0xFFFF * (change['new'] * self.throttle_gain))
            self.motor._pca.channels[4].duty_cycle = 0
            self.motor._pca.channels[7].duty_cycle = int(-0xFFFF * (change['new'] * self.throttle_gain))
            self.motor._pca.channels[6].duty_cycle = 0
            self.motor._pca.channels[5].duty_cycle = 0xFFFF

    def run_port_test():
        import time
        available_i2c_ports = get_available_i2c_ports()
        print("trying steering")
        for each_port in available_i2c_ports:
            try:
                car = NvidiaRacecar(i2c_address1=each_port)
                print(f"    port: {each_port}")
                print(f"    going to 0.3")
                car.steering = 0.3
                time.sleep(0.5)
                print(f"    going to 0.7")
                car.steering = 0.7
                time.sleep(0.5)
            except Exception as error:
                print(error)
        
        print("trying throttle")
        for each_port in available_i2c_ports:
            try:
                car = NvidiaRacecar(i2c_address2=each_port)
                print(f"    port: {each_port}")
                print(f"    going to 0.3")
                car.throttle = 0.3
                time.sleep(0.5)
                print(f"    going to 0.7")
                car.throttle = 0.7
                time.sleep(0.5)
            except Exception as error:
                print(error)

if __name__ == '__main__':
    car = NvidiaRacecar()
    car.run_port_test()
    
    # examples
    car.steering = 0.1
    car.throttle = 0.1
