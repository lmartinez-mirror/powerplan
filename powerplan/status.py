import platform
import subprocess
from time import time
from datetime import datetime

import psutil

from . import cpu
from . import powersupply
from .cpu import CPU, RAPL
from .__init__ import __version__

# Variable string, None's will get filtered out
SYSTEM_INFO = ('\n'+' '*4).join(filter(None, (
    ' '*4+'System',
    f'OS:\t\t\t{platform.platform()}',
    f'powerplan:\t\t{__version__} running on Python{platform.python_version()} with psutil{psutil.__version__}',
    f'CPU model:\t\t{CPU.name}',
    f'Core configuraton:\t{CPU.physical_cores}/{CPU.logical_cores}  {CPU.sibling_cores_repr}',
    f'Frequency range:\t{CPU.freq_range_repr}',
    f'Driver:\t\t{CPU.driver_repr}',
    f'Turbo:\t\t{CPU.turbo_path}',
    f'Governors:\t\t{CPU.governors_repr}',
    f'Policies:\t\t{CPU.policies_repr}' if CPU.policies else None,
    f'Temperature:\t{CPU.temp_sensor_repr}',
    f'AC adapter:\t\t{powersupply.AC.name}' if powersupply.AC.name else None,
    f'Battery:\t\t{powersupply.BAT.name}' if powersupply.BAT.name else None
)))


def show_system_status(profile, monitor_mode=False, ac_power=None):
    '''Prints System status during runtime'''
    if ac_power is None:
        ac_power = powersupply.ac_power()
    power_source = 'AC'+' '*5 if ac_power else 'Battery'
    power_draw = powersupply.BAT.power_draw()
    if (ac_power or power_draw is None):
        power_draw_repr = 'N/A '
    else:
        power_draw_repr = f'{power_draw:.1f}W'

    time_now = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    active_profile = f'{time_now}\t\tActive: {profile.name}'

    # governor/policy
    governor = cpu.read_governor()
    policy = '/'+cpu.read_policy() if CPU.policies else ''
    power_plan = f'Power plan: {governor+policy}'

    power_status = f'Power source: {power_source}\tBattery draw: {power_draw_repr}'
    if RAPL.enabled:
        power_status += f'\tPackage: {RAPL.read_power():.2f}W'

    cores_online = cpu.list_cores('online')
    num_cores_online = len(cores_online)
    # Per cpu stats
    cpus = '\t'.join(['CPU'+str(coreid) for coreid in cpu.list_cores('online')])
    utils = '\t'.join([str(util) for util in psutil.cpu_percent(percpu=True)])

    # Read current frequencies in MHz
    freq_list = cpu.read_current_freq().values()
    avg_freqs = int(sum(freq_list)/num_cores_online)
    freqs = '\t'.join([str(freq) for freq in freq_list])

    # CPU average line
    cpu_cores_turbo = '\t'.join([f'Cores online: {num_cores_online} ',
                                 f"Turbo: {'enabled' if cpu.read_turbo_state() else 'disabled'}"])

    cpu_avg = '\t'.join([f"Avg. Usage: {cpu.read_cpu_utilization('avg')}%",
                         f'Avg. Freq.: {avg_freqs}MHz',
                         f'Package temp: {cpu.read_temperature()}°C'])

    monitor_mode_indicator = '[MONITOR MODE]' if monitor_mode else '[ACTIVE MODE]'
    status_lines = ['',
                    active_profile,
                    power_plan,
                    power_status,
                    cpu_cores_turbo,
                    cpu_avg,
                    '',
                    cpus,
                    utils,
                    freqs]

    subprocess.run('clear')
    print(monitor_mode_indicator)
    print(SYSTEM_INFO)
    print('\n'.join(status_lines))

def print_version():
    print(f'powerplan {__version__}')

def debug_power_info():
    # POWER SUPPLY TREE
    power_supply_tree = powersupply.tree()
    [print('/'.join(info.split('/')[4:])) for info in power_supply_tree.splitlines()]
    print(f'Present temperature sensors: {list(psutil.sensors_temperatures())}')

def read_process_cpu_mem(running_process):
    return running_process.cpu_percent(), running_process.memory_percent()

def debug_runtime_info(process, profile, iteration_start):
    process_util, process_mem = read_process_cpu_mem(process)
    time_iter = (time() - iteration_start) * 1000  # ms
    print(f'Process resources: CPU {process_util:.2f}%, Memory {process_mem:.2f}%, Time {time_iter:.3f}ms')


if __name__ == '__main__':
    debug_power_info()
