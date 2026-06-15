def delete_equipment(data, chaos_name, item_name):
    if chaos_name in data and item_name in data[chaos_name]:
        data[chaos_name].remove(item_name)
        if not data[chaos_name]:
            del data[chaos_name]
    return data