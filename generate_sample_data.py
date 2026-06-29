import random

# Generate sample NSL-KDD format data
protocols = ['tcp', 'udp', 'icmp']
services = ['http', 'smtp', 'ftp', 'ssh', 'telnet', 'dns', 'other']
flags = ['SF', 'S0', 'REJ', 'RSTR', 'RSTO', 'SH', 'OTH']
attack_types = ['normal', 'back', 'land', 'neptune', 'pod', 'smurf', 'teardrop', 'ipsweep', 'nmap', 'portsweep', 'satan', 'ftp_write', 'guess_passwd', 'imap', 'multihop', 'phf', 'spy', 'warezclient', 'warezmaster', 'buffer_overflow', 'loadmodule', 'perl', 'rootkit']

# Generate training data (1000 samples)
with open('data/KDDTrain+.txt', 'w') as f:
    for i in range(1000):
        duration = random.randint(0, 100)
        protocol = random.choice(protocols)
        service = random.choice(services)
        flag = random.choice(flags)
        src_bytes = random.randint(0, 10000)
        dst_bytes = random.randint(0, 10000)
        land = random.randint(0, 1)
        wrong_fragment = random.randint(0, 5)
        urgent = random.randint(0, 5)
        hot = random.randint(0, 100)
        num_failed_logins = random.randint(0, 5)
        logged_in = random.randint(0, 1)
        num_compromised = random.randint(0, 50)
        root_shell = random.randint(0, 1)
        su_attempted = random.randint(0, 2)
        num_root = random.randint(0, 50)
        num_file_creations = random.randint(0, 10)
        num_shells = random.randint(0, 5)
        num_access_files = random.randint(0, 10)
        num_outbound_cmds = random.randint(0, 5)
        is_host_login = random.randint(0, 1)
        is_guest_login = random.randint(0, 1)
        count = random.randint(0, 255)
        srv_count = random.randint(0, 255)
        serror_rate = random.random()
        srv_serror_rate = random.random()
        rerror_rate = random.random()
        srv_rerror_rate = random.random()
        same_srv_rate = random.random()
        diff_srv_rate = random.random()
        srv_diff_host_rate = random.random()
        dst_host_count = random.randint(0, 255)
        dst_host_srv_count = random.randint(0, 255)
        dst_host_same_srv_rate = random.random()
        dst_host_diff_srv_rate = random.random()
        dst_host_same_src_port_rate = random.random()
        dst_host_srv_diff_host_rate = random.random()
        dst_host_serror_rate = random.random()
        dst_host_srv_serror_rate = random.random()
        dst_host_rerror_rate = random.random()
        dst_host_srv_rerror_rate = random.random()
        
        if random.random() < 0.7:
            attack = 'normal'
        else:
            attack = random.choice(attack_types[1:])
        
        line = f'{duration},{protocol},{service},{flag},{src_bytes},{dst_bytes},{land},{wrong_fragment},{urgent},{hot},{num_failed_logins},{logged_in},{num_compromised},{root_shell},{su_attempted},{num_root},{num_file_creations},{num_shells},{num_access_files},{num_outbound_cmds},{is_host_login},{is_guest_login},{count},{srv_count},{serror_rate},{srv_serror_rate},{rerror_rate},{srv_rerror_rate},{same_srv_rate},{diff_srv_rate},{srv_diff_host_rate},{dst_host_count},{dst_host_srv_count},{dst_host_same_srv_rate},{dst_host_diff_srv_rate},{dst_host_same_src_port_rate},{dst_host_srv_diff_host_rate},{dst_host_serror_rate},{dst_host_srv_serror_rate},{dst_host_rerror_rate},{dst_host_srv_rerror_rate},{attack}'
        f.write(line + '\n')

print('Generated KDDTrain+.txt with 1000 samples')

# Generate test data (200 samples)
with open('data/KDDTest+.txt', 'w') as f:
    for i in range(200):
        duration = random.randint(0, 100)
        protocol = random.choice(protocols)
        service = random.choice(services)
        flag = random.choice(flags)
        src_bytes = random.randint(0, 10000)
        dst_bytes = random.randint(0, 10000)
        land = random.randint(0, 1)
        wrong_fragment = random.randint(0, 5)
        urgent = random.randint(0, 5)
        hot = random.randint(0, 100)
        num_failed_logins = random.randint(0, 5)
        logged_in = random.randint(0, 1)
        num_compromised = random.randint(0, 50)
        root_shell = random.randint(0, 1)
        su_attempted = random.randint(0, 2)
        num_root = random.randint(0, 50)
        num_file_creations = random.randint(0, 10)
        num_shells = random.randint(0, 5)
        num_access_files = random.randint(0, 10)
        num_outbound_cmds = random.randint(0, 5)
        is_host_login = random.randint(0, 1)
        is_guest_login = random.randint(0, 1)
        count = random.randint(0, 255)
        srv_count = random.randint(0, 255)
        serror_rate = random.random()
        srv_serror_rate = random.random()
        rerror_rate = random.random()
        srv_rerror_rate = random.random()
        same_srv_rate = random.random()
        diff_srv_rate = random.random()
        srv_diff_host_rate = random.random()
        dst_host_count = random.randint(0, 255)
        dst_host_srv_count = random.randint(0, 255)
        dst_host_same_srv_rate = random.random()
        dst_host_diff_srv_rate = random.random()
        dst_host_same_src_port_rate = random.random()
        dst_host_srv_diff_host_rate = random.random()
        dst_host_serror_rate = random.random()
        dst_host_srv_serror_rate = random.random()
        dst_host_rerror_rate = random.random()
        dst_host_srv_rerror_rate = random.random()
        
        if random.random() < 0.7:
            attack = 'normal'
        else:
            attack = random.choice(attack_types[1:])
        
        line = f'{duration},{protocol},{service},{flag},{src_bytes},{dst_bytes},{land},{wrong_fragment},{urgent},{hot},{num_failed_logins},{logged_in},{num_compromised},{root_shell},{su_attempted},{num_root},{num_file_creations},{num_shells},{num_access_files},{num_outbound_cmds},{is_host_login},{is_guest_login},{count},{srv_count},{serror_rate},{srv_serror_rate},{rerror_rate},{srv_rerror_rate},{same_srv_rate},{diff_srv_rate},{srv_diff_host_rate},{dst_host_count},{dst_host_srv_count},{dst_host_same_srv_rate},{dst_host_diff_srv_rate},{dst_host_same_src_port_rate},{dst_host_srv_diff_host_rate},{dst_host_serror_rate},{dst_host_srv_serror_rate},{dst_host_rerror_rate},{dst_host_srv_rerror_rate},{attack}'
        f.write(line + '\n')

print('Generated KDDTest+.txt with 200 samples')
