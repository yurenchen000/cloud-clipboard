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
            receivedLoading: true,
            receivedBuffer: [],   //延迟渲染的历史数据(receiveMultiOld), 用户点"加载更多"才渲染
            bulkRendering: false, //正在分块渲染(用于临时关闭过渡动画)
            bulkDone: 0,          //分块渲染进度: 已渲染条数
            bulkTotal: 0,         //分块渲染进度: 总条数
            event: {
                //add to latest
                receive: data => {
                    //冻结数据, 跳过 Vue 深层响应式劫持(列表项只读)
                    this.$root.received.unshift(Object.freeze(data));
                },
                //add to latest, data item old first
                receiveMulti: data => {
                    console.log('--- render first page directly')
                    this.receivedLoading = true;
                    // this.$root.received.unshift(...Array.from(data).reverse());
                    this.appendChunked(Array.from(data).reverse(), 'unshift');
                },
                //add to oldest, data item old first
                receiveMultiOld: data => {
                    //不再自动渲染历史(旧)数据: 先缓存到 receivedBuffer,
                    //由用户点击"加载更多"按钮时再分块渲染, 规避移动端主线程阻塞.
                    this.receivedBuffer.push(...Array.from(data).reverse());
                    this.receivedLoading = false; //首屏(第一页)已就绪
                },
                revoke: data => {
                    let index = this.$root.received.findIndex(e => e.id === data.id);
                    if (index !== -1) this.$root.received.splice(index, 1);
                    //同时从未渲染的缓存里移除(可能还没被"加载更多"渲染出来)
                    let bufIndex = this.receivedBuffer.findIndex(e => e.id === data.id);
                    if (bufIndex !== -1) this.receivedBuffer.splice(bufIndex, 1);
                },
                config: data => {
                    this.retry = 0; //real success login
                    this.$root.config = data;
                    this.receivedLoading = true;
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
                    localStorage.setItem('need_auth', true);
                },
            },
        };
    },
    computed: {
        //分块渲染进度百分比: 供全局 $root.bulkPercent 使用(App.vue 悬浮进度条等)
        bulkPercent() {
            return this.bulkTotal ? Math.round(100 * this.bulkDone / this.bulkTotal) : 0;
        },
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
                timeout: -1,
            });
            console.log('0. req server:', performance.now())

            // A fake_http just skip get /server
            const fake_server = {
                get(url){
                    return new Promise((resolve, reject) => {
                        return resolve({
                          data: {//guess server config
                            // server: location.origin.replace(/^http/,'ws')+'/push',
                            server: location.origin.replace(/^http/,'ws')+location.pathname.replace(/\/$/,'')+'/push',
                            auth: !!(localStorage.getItem('auth') || localStorage.getItem('need_auth')),
                            status: 200,
                          }
                        })
                        //fake http never reject
                    });
                }
            };

            let skip_server = true;
            // this.$http.get('server').then(response => {
            (skip_server? fake_server: this.$http).get('server').then(response => {
                if (this.authCode) localStorage.setItem('auth', this.authCode);
                return new Promise((resolve, reject) => {
                    console.log('1. ack server:', performance.now())
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
                    console.log('1. req push:', performance.now())
                    const ws = new WebSocket(wsUrl);
                    ws.onopen = () => resolve(ws);
                    ws.onerror = reject;
                    // console.log('1. onopen, onerr set.');
                });
            }).then((/** @type {WebSocket} */ ws) => {
                this.websocketConnecting = false;
                // this.retry = 0;
                this.cancelChunkFrame();
                this.received = [];
                this.receivedBuffer = [];
                console.log('2. ack push:', performance.now())
                this.$toast(this.$t('connectSuccess'));
                // setInterval(() => {ws.send('')}, 30000);
                ws.interval = setInterval(() => {
                    // console.log('== ws interval:', ws, ws.interval)
                    ws.send('')
                }, 30000);
                ws.onclose = (e) => {
                    console.log('== ws.onclose:', ws, e)
                    clearInterval(ws.interval)
                    this.failure()
                };
                ws.onerror = (e) => {
                    console.log('== ws.onerror:', ws, e)
                };
                ws.onmessage = e => {
                    try {
                        let parsed = JSON.parse(e.data);
                        (this.event[parsed.event] || (() => {}))(parsed.data);
                    } catch {}
                };
                this.websocket = ws;
            }).catch(error => {
                console.log('++ ws.onerror:', error);
                this.websocketConnecting = false;
                this.failure();
            });
        },
        disconnect() {
            this.websocketConnecting = false;
            this.cancelChunkFrame();
            if (this.websocket) {
                this.websocket.onclose = () => {};
                this.websocket.close();
                this.websocket = null;
            }
            this.$root.device = [];
        },
        cancelChunkFrame() {
            //令牌自增, 使仍在排队(未执行)的 step/nextTick 回调失效, 避免重入重复渲染
            this._chunkToken = (this._chunkToken || 0) + 1;
            cancelAnimationFrame(this._chunkFrame);
            this._chunkFrame = null;
            this.receivedLoading = false;
            this.bulkRendering = false;
        },
        //把缓存的历史数据(receiveMultiOld)渲染出来: 用户点击"加载更多"时调用
        loadBuffered() {
            if (!this.receivedBuffer.length || this.bulkRendering) return;
            const items = this.receivedBuffer;
            this.receivedBuffer = []; //先清空, 渲染过程中按钮消失
            this.appendChunked(items, 'push');
        },
        /**
         * 自适应时间分块渲染: 每帧只渲染"约 frameBudget 毫秒"能处理的条数,
         * 帧与帧之间用 requestAnimationFrame 让出主线程 -> 加载过程中按钮仍可点击.
         * @param {Array} items 已按目标顺序排好的数据
         * @param {'push'|'unshift'} mode push=追加到列表底部, unshift=插入到列表顶部
         */
        appendChunked(items, mode = 'push', opts = {}) {
            this.cancelChunkFrame();
            if (!Array.isArray(items) || !items.length) {
                this.bulkDone = this.bulkTotal = 0;
                if (opts.onDone) opts.onDone();
                return;
            }
            const token = this._chunkToken;
            const received = this.$root.received;
            const freeze = opts.freeze !== false;       //冻结每条数据, 跳过 Vue 深层响应式劫持
            const frameBudget = opts.frameBudget || 10;  //每帧目标耗时(ms)
            const MIN_CHUNK = 6, MAX_CHUNK = 300;
            let chunkSize = opts.initialChunk || 24;     //首帧先保守一点
            let index = 0;
            let insertPos = 0; //unshift 模式下的移动插入位置, 保证批次间顺序正确

            this.receivedLoading = true;
            this.bulkRendering = true;
            this.bulkTotal = items.length;
            this.bulkDone = 0;

            const step = () => {
                if (token !== this._chunkToken) return; //已被取消/被新任务取代
                const t0 = performance.now();
                const end = Math.min(index + chunkSize, items.length);
                const batch = items.slice(index, end);
                index = end;
                if (freeze) {
                    for (let i = 0; i < batch.length; i++) Object.freeze(batch[i]);
                }
                if (mode === 'unshift') {
                    received.splice(insertPos, 0, ...batch);
                    insertPos += batch.length;
                } else {
                    received.push(...batch);
                }
                this.bulkDone = index;
                //等 DOM 更新(nextTick)后再测量, 这样耗时包含"push + 组件创建/渲染"
                this.$nextTick(() => {
                    if (token !== this._chunkToken) return;
                    const dt = performance.now() - t0;
                    if (dt > 0) {
                        //根据实测耗时调整下一帧条数, 向 frameBudget 收敛(带阻尼);
                        //dt 极小时 adapted 会很大, 但被 MAX_CHUNK 夹住, 不会溢出
                        const adapted = Math.round(chunkSize * (frameBudget / dt));
                        chunkSize = Math.round((chunkSize + adapted) / 2);
                        chunkSize = Math.max(MIN_CHUNK, Math.min(MAX_CHUNK, chunkSize));
                    }
                    if (index < items.length) {
                        this._chunkFrame = requestAnimationFrame(step);
                    } else {
                        this._chunkFrame = null;
                        this.receivedLoading = false;
                        this.bulkRendering = false;
                        this.bulkDone = this.bulkTotal = 0;
                        if (opts.onDone) opts.onDone();
                    }
                });
            };
            step();
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
                    timeout: -1,
                });
            }
        },
    },
    mounted() {
        this.connect();
    },
}
