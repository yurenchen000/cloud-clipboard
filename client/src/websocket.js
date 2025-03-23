export default {
    data() {
        return {
            websocket: null,
            websocketConnecting: false,
            authCode: localStorage.getItem('auth') || '',
            authCodeDialog: false,
            room: this.$router.currentRoute.query.room || '',
            roomInput: '',
            roomDialog: false,
            retry: 0,
            event: {
                //add to latest
                receive: data => {
                    this.$root.received.unshift(data);
                },
                //add to latest, data item old first
                receiveMulti: data => {
                    this.$root.received.unshift(...Array.from(data).reverse());
                },
                //add to oldest, data item old first
                receiveMultiOld: data => {
                    this.$root.received.push(...Array.from(data).reverse());
                },
                revoke: data => {
                    let index = this.$root.received.findIndex(e => e.id === data.id);
                    if (index === -1) return;
                    this.$root.received.splice(index, 1);
                },
                config: data => {
                    this.$root.config = data;
                    console.log(
                        `%c Cloud Clipboard ${data.version} by TransparentLC %c https://github.com/TransparentLC/cloud-clipboard `,
                        'color:#fff;background-color:#1e88e5',
                        'color:#fff;background-color:#64b5f6'
                    );
                },
                connect: data => {
                    this.$root.device.push(data);
                },
                disconnect: data => {
                    let index = this.$root.device.findIndex(e => e.id === data.id);
                    if (index === -1) return;
                    this.$root.device.splice(index, 1);
                },
                forbidden: () => {
                    this.authCode = '';
                    localStorage.removeItem('auth');
                },
            },
        };
    },
    watch: {
        room() {
            this.disconnect();
            this.connect();
        },
    },
    methods: {
        connect() {
            this.websocketConnecting = true;
            this.$toast(this.retry ? this.$t('isReConnecting', {retry: this.retry}) : this.$t('isConnecting'), {
                showClose: false,
                dismissable: false,
                timeout: 0,
            });
            this.$http.get('server').then(response => {
                if (this.authCode) localStorage.setItem('auth', this.authCode);
                return new Promise((resolve, reject) => {
                    const wsUrl = new URL(response.data.server);
                    wsUrl.protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
                    wsUrl.port = location.port;
                    if (response.data.auth) {
                        if (this.authCode) {
                            wsUrl.searchParams.set('auth', this.authCode);
                        } else {
                            this.authCodeDialog = true;
                            return;
                        }
                    }
                    wsUrl.searchParams.set('room', this.room);
                    const ws = new WebSocket(wsUrl);
                    ws.onopen = () => resolve(ws);
                    ws.onerror = reject;
                });
            }).then((/** @type {WebSocket} */ ws) => {
                this.websocketConnecting = false;
                this.retry = 0;
                this.received = [];
                this.$toast(this.$t('connectSuccess'));
                setInterval(() => {ws.send('')}, 30000);
                ws.onclose = () => {this.failure()};
                ws.onmessage = e => {
                    try {
                        let parsed = JSON.parse(e.data);
                        (this.event[parsed.event] || (() => {}))(parsed.data);
                    } catch {}
                };
                this.websocket = ws;
            }).catch(error => {
                // console.log(error);
                this.websocketConnecting = false;
                this.failure();
            });
        },
        disconnect() {
            this.websocketConnecting = false;
            if (this.websocket) {
                this.websocket.onclose = () => {};
                this.websocket.close();
                this.websocket = null;
            }
            this.$root.device = [];
        },
        failure() {
            this.websocket = null;
            this.$root.device = [];
            if (this.retry++ < 3) {
                this.connect();
            } else {
                this.$toast.error(this.$t('connectFailed_clickToConnect'), {
                    showClose: false,
                    dismissable: false,
                    timeout: 0,
                });
            }
        },
    },
    mounted() {
        this.connect();
    },
}
