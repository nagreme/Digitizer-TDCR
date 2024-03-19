import sys
import pdb

filename = sys.argv[1]

# column indices
INDEX_CHANNEL_NUM = 0
INDEX_LONG_GATE = 1
INDEX_SHORT_GATE = 2
INDEX_TIMESTAMP = 3
INDEX_TIME = 4
INDEX_DELTA_TIME = 5


class DataPoint:
    def __init__(self, channel_num, long_gate, short_gate, timestamp, time_ms, delta_time):
        self.channel_num = channel_num
        self.long_gate = long_gate
        self.short_gate = short_gate
        self.timestamp = timestamp
        self.time = time_ms
        self.delta_time = delta_time
    
    def __str__(self):
        return f"DataPoint{self.__dict__}"
    
    def __repr__(self):
        # return f"DataPoint{self.__dict__}"
        return f"(chNum={self.channel_num}, time={self.timestamp})"
    
    def __eq__(self, other):
        if isinstance(other, DataPoint):
            return self.channel_num == other.channel_num
        else:
            return False
    
    def __hash__(self):
        return hash(self.channel_num)


timestamp_indexed_dict = {}
timestamp_set = set()


def build_dictionary(dead_time=0, gate_cutoff=2500, ratio_cutoff=0):
    # this auto closes the file object at the end of the block
    with open(filename) as file:
        # read one file at a time
        for line in file:
            # extract data
            columns = line.split()
            channel_num = int(columns[INDEX_CHANNEL_NUM])
            long_gate = int(columns[INDEX_LONG_GATE])
            short_gate = int(columns[INDEX_SHORT_GATE])
            timestamp = int(columns[INDEX_TIMESTAMP])
            time = float(columns[INDEX_TIME])
            delta_time = float(columns[INDEX_DELTA_TIME])
            
            # filtering
            if delta_time < dead_time or long_gate < gate_cutoff or short_gate/long_gate < ratio_cutoff:
                continue
            
            # build object
            data_point = DataPoint(channel_num, long_gate, short_gate, timestamp, time, delta_time)
            
            # if we haven't seen this timestamp yet init with empty list
            if timestamp not in timestamp_indexed_dict:
                timestamp_indexed_dict[timestamp] = []
            
            # add your data point to the dictionary
            timestamp_indexed_dict[timestamp].append(data_point)
            
            # append timestamp to masterlist
            timestamp_set.add(timestamp)
    
    
def main():
    dead_times = [0]
    gate_cutoff = 2500
    ratio_cutoff = 0
    coincidence_times = range(50, 150, 10)
    
    for dead_time in dead_times:
        build_dictionary(dead_time)
        
        for ct in coincidence_times:
            # bucket timestamps by coincidence_time
            timestamp_groups = []
            curr_group = []
            timestamp_list = sorted(timestamp_set)
            for timestamp in timestamp_list:
                # starting a new group (first element)
                if not curr_group: # is empty
                    curr_group.append(timestamp)
                # check if we need to append to the current group of if we create a new one
                else:
                    if timestamp - curr_group[0] < ct:
                        curr_group.append(timestamp)
                    else:
                        timestamp_groups.append(curr_group)
                        curr_group = [timestamp]
                        
            # rebuild a dict based on the new timestamp buckets
            timestamp_group_dict = {}
            
            for group in timestamp_groups:
                timestamp = group[0]
                timestamp_group_dict[timestamp] = set()
                for member in group:
                    timestamp_group_dict[timestamp].update(timestamp_indexed_dict[member])
                
            # output result summary
            counts = {
                'single': 0,
                'double': 0,
                'double_01': 0,
                'double_12': 0,
                'double_02': 0,
                'triple': 0
            }
            for timestamp, data_point_set in timestamp_group_dict.items():
                coincidences = len(data_point_set)
                data_point_list = list(data_point_set)

                if coincidences == 1:
                    counts['single'] += 1
                elif coincidences == 2:
                    counts['double'] += 1
                    first_ch = data_point_list[0].channel_num
                    second_ch = data_point_list[1].channel_num
                    double_ch_str = f'{first_ch}{second_ch}' if first_ch < second_ch else f'{second_ch}{first_ch}'
                    counts[f'double_{double_ch_str}'] += 1
                elif coincidences == 3:
                    counts['triple'] += 1
                else:
                    print("something weird happened: ")
                    print(data_point_set)

                # print(f'timestamp={k}: {len(v)}')
            print(f"coincidence time={ct} => counts={counts}")
            
    
    
    
if __name__ == '__main__':
    main()
