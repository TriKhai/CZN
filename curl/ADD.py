def add_equipment(data, chaos_name, item_name):
    if chaos_name not in data:
        data[chaos_name] = []
    if item_name not in data[chaos_name]:
        data[chaos_name].append(item_name)
    return data