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

const iface = <interface name="net.screenfreeze.desktopconnector">
<method name="stats">
<arg type="s" direction="out" name="json" />
</method>
<method name="notification">
<arg type="s" direction="out" name="text" />
</method>
<method name="compose_sms">
<arg type="s" direction="in" name="ip" />
</method>
<signal name="changed" />
<signal name="new_notification" />
</interface>


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
    composesms: function(ip) {
        let parameters = new GLib.Variant('(s)', [ip]);
        this.proxy.call_sync('compose_sms', parameters, 0, 1000, null);
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

            let deviceItem = new PhonesMenuItem(phone);
            regPhones[phone.uuid] = deviceItem;
            _indicator.menu.addMenuItem(deviceItem);
            _indicator.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
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

const PhonesMenuItem = new Lang.Class({
    Name: 'PhonesMenuItem',
    Extends: PopupMenu.PopupBaseMenuItem,  

    _init: function(info) {
	    this.parent({reactive: false});
	    this._info = info;

        let missedmsgsstr = "";
        let missedcallsstr = "";

        this._ip = info.ip;
        this._port = info.port;
        let can_message = info.canmessage;

        //missedstrs
        if (info.missedsmscount > 0) { missedmsgsstr = "unread Messages "+ info.missedsmscount; }
        if (info.missedcallcount > 0) { missedcallsstr = "missed Calls "+ info.missedcallcount; }

        //Batterystring
        let batterystr = "Battery:  "+info.battery+"%";        
        if (info.batterystate) {
            batterystr += " (*)";
        }

        //Volumestring
        let volumestr = "Volume:  "+info.volume+"%     ";

        //used Storagestring
        let storagestr = "Storage:  "+info.storage+"%     ";

        this.vbox = new St.BoxLayout({vertical: true });
        this.stathbox = new St.BoxLayout({vertical: false});
        this.missedhbox = new St.BoxLayout({vertical: false});
        this.namelabel = new St.Label({ text: info.name, style_class: 'device-label' });
        this.vollabel = new St.Label({ text: volumestr });
        this.batlabel = new St.Label({ text: batterystr });
        this.storagelabel = new St.Label({ text: storagestr });

        this.missedcallslabel = new St.Label({ text: missedcallsstr });
        this.missedmsgslabel = new St.Label({ text: missedmsgsstr });
        this.notificationslabel = new St.Label({ text: "Notifications", style_class: 'notifications-label' });
        this.notificationsvbox = new St.BoxLayout({vertical: true, style_class: 'notifications-box'});
        
        this.missedhbox.add(this.missedmsgslabel);
        this.missedhbox.add(this.missedcallslabel);
        this.stathbox.add(this.vollabel);
        this.stathbox.add(this.batlabel);

        this.compbutton = new St.Button({style_class: 'notification-icon-button',label: "Compose Message..."}); 
        this.compbutton.connect('clicked', Lang.bind(this, this.composemsg));
        this.vbox.add(this.namelabel);
        this.vbox.add(this.stathbox);        
        this.vbox.add(this.storagelabel);  
        this.vbox.add(this.missedhbox);
        this.vbox.add(this.notificationslabel);
        this.vbox.add(this.notificationsvbox, { x_fill: true, expand: false });
        
        if (can_message) {
            this.vbox.add(this.compbutton, { x_fill: true, expand: true });
        }
        
        // GS 3.8 support
        if (shellversion[1] == 10) {
            this.actor.add_child(this.vbox, { expand: true });
        }
        else {
            this.addActor(this.vbox, { expand: true });
        }        
    },

    destroy: function() {
        this.parent();
    },

    activate: function(event) {
	    this.parent(event);
    },

    composemsg: function(event) {
        dbusclient.composesms(this._ip);
        _indicator.menu.close();
    },

    addnotification: function(text) {
        let n = new St.Button({style_class: 'panel-button', label: text, 
                style: 'border: 1px solid grey; font-size: 1em; font-weight: normal; padding-left:0.2em;' });
        n.set_alignment(St.Align.START, St.Align.START);
        n.connect('clicked', Lang.bind(this, function() { n.destroy(); }));
        this.notificationsvbox.add(n, { x_fill: true, expand: false });
    },

    update: function(info) {
        //Batterystring
        let batterystr = "Battery:  "+info.battery+"%";        
        if (info.batterystate) {
            batterystr += " (*)";
        }

        //Volumestring
        let volumestr = "Volume:  "+info.volume+"%    ";
        
        //used Storagestring
        let storagestr = "Storage:  "+info.storage+"%     ";

        //missedstrs
        let missedmsgsstr = "";
        let missedcallsstr = "";
        if (info.missedsmscount > 0) { missedmsgsstr = "unread Messages "+ info.missedsmscount; }
        if (info.missedcallcount > 0) { missedcallsstr = "missed Calls "+ info.missedcallcount; }

        this.batlabel.set_text(batterystr);
        this.vollabel.set_text(volumestr);
        this.storagelabel.set_text(storagestr);
        this.missedcallslabel.set_text(missedcallsstr);
        this.missedmsgslabel.set_text(missedmsgsstr);
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
    },

    show: function() {
        this.actor.show();
        updatehandler();        
    },

    destroy: function() {
        this.parent();
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
