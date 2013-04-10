import_ok = True

try:
    import weechat as wee
except:
    print("No! Bad user!")
    import_ok = False

NAME = "buffer_priority"
AUTHOR = "numeral <numerical@gmail.com>"
VERSION = "0.10"
LICENSE = "GPL3"
DESCRIPTION = "This plugin attempts to be the end all of buffer placement."

conf_opt = "plist"
conf_opt2 = "main_top"

buffers = {} # Hold all the buffers in a dict
maintop = True

# Python2Weechat
def py2wee(dictionary):
    return ' '.join(list(map(lambda x: str(x) + " " + str(dictionary[x]), dictionary)))

# Weechat2Python
def wee2py(string):
    string = string.split()
    assert(len(string) % 2 == 0)
    d = {}
    for i in range(0, len(string), 2):
        try:
            d[string[i]] = int(string[i+1])
        except ValueError:
            pass

    return d

# Save
def save_state():
    global buffers
    global maintop
    if(len(buffers)):
        wee.config_set_plugin(conf_opt, py2wee(buffers))
        wee.config_set_plugin(conf_opt2, str(maintop))

    return

# Load
def load_state():
    global buffers
    global maintop
    if wee.config_is_set_plugin(conf_opt):
        buffers = wee2py(wee.config_get_plugin(conf_opt))
        maintop = bool(wee.config_get_plugin(conf_opt2))
    else:
        buffers = {}
        maintop = True

    return


def reorder_buffers():
    global buffers
    bufcopy = dict(buffers)
    priolist = []
    while len(bufcopy):
        priolist.append(max(bufcopy, key=bufcopy.get))
        bufcopy.pop(max(bufcopy, key=bufcopy.get))
    pointerlist = {}
    infolist = wee.infolist_get("buffer", "", "")
    while wee.infolist_next(infolist): # go through the buffers and jot down relevant pointers
        for name in priolist:
            try:
                bufname = wee.infolist_string(infolist, "name").split('.', 1)[1]
            except IndexError:
                bufname = wee.infolist_string(infolist, "name")
            if name == bufname:
                if name in pointerlist:
                    pointerlist[name].append(
                            wee.infolist_pointer(infolist, "pointer"))
                else:
                    pointerlist[name] = [wee.infolist_pointer(
                        infolist, "pointer")]

    index = 1
    if(maintop):
        index += 1
    for name in priolist:
        if name in pointerlist:
            for pointer in pointerlist[name]:
                wee.buffer_set(pointer, "number", str(index))
                index += 1
    return

def reorder_cb(data, signal, signal_data):
    reorder_buffers()
    return wee.WEECHAT_RC_OK

def bpriority_add(dub):
    global buffers
    if(len(dub) != 2):
        return
    try:
        prio = int(dub[1])
    except ValueError:
        wee.prnt("", "Error: %s is not a number" % dub[1])
        return
    if(dub[0] in buffers):
        wee.prnt("", "Changing priority of %s to %d" % (dub[0], prio))
        buffers[dub[0]] = prio
    else:
        wee.prnt("", "Added %s with priority %d" % (dub[0], prio))
        buffers[dub[0]] =  prio
    reorder_buffers()
    save_state()
    return

def bpriority_del(dub):
    global buffers
    if(len(dub) != 1):
        wee.prnt("", "Incorrect number of arguments for delete command")
        return

    if dub[0].lower() == "all":
        buffers = {}
        wee.prnt("", "Cleared priority list")
        save_state()
        return

    if dub[0] not in buffers:
        wee.prnt("", "That buffer has no priority")
        return

    wee.prnt("", "Removed %s from the list of priorities" % (dub[0]))
    buffers.pop(dub[0])
    save_state()
    reorder_buffers()
    return

def bpriority_list():
    global buffers
    wee.prnt("", str(buffers))
    reorder_buffers();
    return

# Cmd
def bpriority_cmd(data, buffer, args):
    dub = args.split(' ')
    if(dub[0] == "add"):
        bpriority_add(dub[1:])
    elif(dub[0] == "del"):
        bpriority_del(dub[1:])
    elif(dub[0] == "list"):
        bpriority_list()
    else:
        return wee.WEECHAT_RC_ERROR

    return wee.WEECHAT_RC_OK

# Register
if __name__ == "__main__" and import_ok:
    if wee.register(NAME, AUTHOR, VERSION, LICENSE, DESCRIPTION, "", ""):
        wee.hook_command(
                "bpriority", # command
                "Change buffer priorities", # description
                "[list] || [add buffer priority] || [del buffer|all]", # args
                " add: adds a channel with a priority(0-999)\n"
                " del: deletes a buffer from the priority system\n", # arg desc
                "add del", # completions
                "bpriority_cmd", "")
        load_state()
        wee.hook_signal("buffer_opened", "reorder_cb", "")
        reorder_buffers()

