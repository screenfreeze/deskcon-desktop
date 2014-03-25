const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Lang = imports.lang;
const Shell = imports.gi.Shell;
const St = imports.gi.St;

const Main = imports.ui.main;
const PanelMenu = imports.ui.panelMenu;
const PopupMenu = imports.ui.popupMenu;
const Panel = imports.ui.panel;
const Tweener = imports.ui.tweener;

const iface = '<node> \
    <interface name="net.screenfreeze.desktopconnector"> \
        <method name="stats"> \
            <arg type="s" direction="out" name="json" /> \
        </method> \
        <method name="notification"> \
            <arg type="s" direction="out" name="text" /> \
        </method> \
        <method name="compose_sms"> \
            <arg type="s" direction="in" name="host" /> \
        </method> \
        <method name="ping_device"> \
            <arg type="s" direction="in" name="host" /> \
        </method> \
        <method name="send_file"> \
            <arg type="s" direction="in" name="host" /> \
        </method> \
        <method name="show_settings"> \
        </method> \
        <method name="setup_device"> \
        </method> \
        <signal name="changed" /> \
        <signal name="new_notification" /> \
    </interface> \
</node>';


const DBusClient = new Lang.Class({
    Name: 'DBusClient',
    _init: function() {
        this.ProxyClass = Gio.DBusProxy.makeProxyWrapper(iface);
 
        this.proxy = new this.ProxyClass(Gio.DBus.session,
                        'net.screenfreeze.desktopconnector',
                        '/net/screenfreeze/desktopconnector', Lang.bind(this, this._onError));
        this.changesig = this.proxy.connectSignal("changed", updatehandler);
        this.notificationsig = this.proxy.connectSignal("new_notification", notificationhandler);
    },
    _onError: function(obj, error) {
        if (error) {
            print('error :',error);
        }
    },
    destroy: function() {
        this.proxy.disconnectSignal(this.changesig);
        this.proxy.disconnectSignal(this.notificationsig);
    },
    getProxy: function() {
        return this.proxy;
    },
    getStats: function() {
        let info = this.proxy.call_sync('stats', null, 0, 1000, null);
        let ui = info.get_child_value(0);
        let jsonstr = ui.get_string()[0];
        return jsonstr;
    },
    getNotification: function() {
        let info = this.proxy.call_sync('notification', null, 0, 1000, null);
        let ui = info.get_child_value(0);
        let jsonstr = ui.get_string()[0];
        return jsonstr;
    },
    composesms: function(ip, port) {
        host = ip + ":" + port;
        let parameters = new GLib.Variant('(s)', [host]);
        this.proxy.call_sync('compose_sms', parameters, 0, 1000, null);
    },
    pingdevice: function(ip, port) {
        host = ip + ":" + port;
        let parameters = new GLib.Variant('(s)', [host]);
        this.proxy.call_sync('ping_device', parameters, 0, 1000, null);
    },
    sendfile: function(ip, port) {
        host = ip + ":" + port;
        let parameters = new GLib.Variant('(s)', [host]);
        this.proxy.call_sync('send_file', parameters, 0, 1000, null);
    },
    showsettings: function() {
        this.proxy.call_sync('show_settings', null, 0, 1000, null);
    },
    setupdevice: function() {
        this.proxy.call_sync('setup_device', null, 0, 1000, null);
    },
});

function updatehandler() {
    let jsonstr = "{}";
    try {
        jsonstr = dbusclient.getStats();
    } catch (e) {
        jsonstr = "{}";
    }

    let phonesObject = JSON.parse(jsonstr);

    let phonesArray = phonesObject.phones;

    for (var pos in phonesArray) {
        let phone = phonesArray[pos];

        //test if phone is already in Menu
        if (regPhones[phone.uuid] == undefined) {

            let deviceItem = new DeviceMenuItem(phone);
            regPhones[phone.uuid] = deviceItem;

            _indicator.menu.addMenuItem(deviceItem.infoitem, 0);
            _indicator.menu.addMenuItem(deviceItem.notificationsmenuitem, 1);
            _indicator.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem(), 2);

        }
        else {
            regPhones[phone.uuid].update(phone);
        }       
    }    
}

function notificationhandler() {
    let not = dbusclient.getNotification().split("::", 2);
    let uuid = not[0];
    let text = not[1];

    if (regPhones[uuid] == undefined) {

    }
    else {
        regPhones[uuid].addnotification(text);
    }   
}

const DeviceMenuItem = new Lang.Class({
    Name: 'DeviceMenuItem',

    _init: function(info) {
        this.infoitem = new PopupMenu.PopupSubMenuMenuItem(info.name);
        let pingb = new PopupMenu.PopupMenuItem("Ping");
        let sendfileb = new PopupMenu.PopupMenuItem("Send File(s)");
        let composeb = new PopupMenu.PopupMenuItem("Compose Message");
        composeb.connect('activate', Lang.bind(this, this.composemsg));
        pingb.connect('activate', Lang.bind(this, this.ping));
        sendfileb.connect('activate', Lang.bind(this, this.sendfile));

        this._ip = info.ip;
        this._port = info.controlport;
        let can_message = info.canmessage;

        if (can_message) {
            this.infoitem.menu.addMenuItem(composeb);
        }        
        this.infoitem.menu.addMenuItem(sendfileb);        
        this.infoitem.menu.addMenuItem(pingb);

        this.notificationsmenuitem = new PopupMenu.PopupSubMenuMenuItem("Notifications");
        let clearb = new PopupMenu.PopupMenuItem("Clear");
        clearb.connect('activate', Lang.bind(this, this.clearnotifications));
        this.notifcationsArray = new Array();
        this.notificationsmenuitem.menu.addMenuItem(clearb);
        this.notificationsmenuitem.actor.hide()
        this.update(info)
    },

    composemsg: function(event) {
        dbusclient.composesms(this._ip, this._port);
        _indicator.menu.close();
    },

    ping: function(event) {
        dbusclient.pingdevice(this._ip, this._port);
        _indicator.menu.close();
    },

    sendfile: function(event) {
        dbusclient.sendfile(this._ip, this._port);
        _indicator.menu.close();
    },

    addnotification: function(text) {
        let newnot = new PopupMenu.PopupMenuItem(text, {reactive: false});
        this.notifcationsArray.push(newnot);
        newnot.connect('clicked', Lang.bind(this, function() { newnot.destroy(); }));
        this.notificationsmenuitem.menu.addMenuItem(newnot, 0);
        this.notificationsmenuitem.actor.show();
    },

    clearnotifications: function() {
        for (i=0;i<this.notifcationsArray.length;i++) {
            let not = this.notifcationsArray.pop();
            not.destroy();
        }
        this.notificationsmenuitem.actor.hide();
    },

    update: function(info) {
        let name = info.name

        //Batterystring
        let batterystr = "Bat:  "+info.battery+"%";        
        if (info.batterystate) {
            batterystr += " (*)";
        }

        //Volumestring
        let volumestr = "Vol:  "+info.volume+"%";
        
        //used Storagestring
        let storagestr = "Str:  "+info.storage+"%";

        //missedstrs
        let missedmsgsstr = "";
        let missedcallsstr = "";
        if (info.missedsmscount > 0) { missedmsgsstr = "unread Messages "+ info.missedsmscount; }
        if (info.missedcallcount > 0) { missedcallsstr = "missed Calls "+ info.missedcallcount; }

        let newtxt = (name+"\n"+batterystr+" / "+volumestr+" / "+storagestr);

        if (missedmsgsstr != "") {
            newtxt = newtxt+"\n"+missedmsgsstr
        }
        if (missedcallsstr != "") {
            newtxt = newtxt+"\n"+missedcallsstr
        }

        this.infoitem.label.set_text(newtxt);
    },
});

const PhonesMenu = new Lang.Class({
    Name: 'PhonesMenu.PhoneMenu',
    Extends: PanelMenu.Button,

    _init: function() {
        this.parent(0.0, 'PhoneMenu');
        let hbox = new St.BoxLayout({ style_class: 'panel-status-menu-box' });
        let icon = new St.Icon({ icon_name: 'sphone-symbolic',
                                 style_class: 'system-status-icon' });

        hbox.add_child(icon);
        this.actor.add_child(hbox);

        let settingsbutton = new PopupMenu.PopupMenuItem("Settings");
        let setupdevicebutton = new PopupMenu.PopupMenuItem("Setup new Device");

        settingsbutton.connect('activate', Lang.bind(this, this.show_settings));
        setupdevicebutton.connect('activate', Lang.bind(this, this.setup_device));
        this.menu.addMenuItem(setupdevicebutton);
        this.menu.addMenuItem(settingsbutton);

        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
    },

    show: function() {
        this.actor.show();
        updatehandler();        
    },

    destroy: function() {
        this.parent();
    },

    show_settings: function() {
        dbusclient.showsettings();
    },

    setup_device: function() {
        dbusclient.setupdevice();
    },

});

// GS 3.8
const PhonesMenuOld = new Lang.Class({
    Name: 'PhonesMenu.PhoneMenu',
    Extends: PanelMenu.SystemStatusButton,

    _init: function() {
        this.parent('sphone-symbolic');
    },

    show: function() {
        this.actor.show();
        updatehandler();        
    },

    destroy: function() {
        this.parent();
    },

});


function init(extensionMeta) {
    let theme = imports.gi.Gtk.IconTheme.get_default();
    theme.append_search_path(extensionMeta.path + "/icons");
}

let _indicator;
let regPhones = {};
let dbusclient;
let shellversion;

function enable() {
    dbusclient = new DBusClient();
    shellversion = imports.misc.config.PACKAGE_VERSION.split(".").map(function (x) { return +x; })
    
    // GS 3.8 support
    if (shellversion[1] == 10) {
        _indicator = new PhonesMenu; 
    }
    else {
        _indicator = new PhonesMenuOld;
    }  

    Main.panel.addToStatusArea('phonesMenu', _indicator, 1);
    
    updatehandler();
}

function disable() {
    dbusclient.destroy();    
    _indicator.destroy();
    regPhones = {};
}

