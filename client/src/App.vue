<template>
    <v-app>
        <v-navigation-drawer
            v-model="drawer"
            temporary
            app
        >
            <v-list>
                <v-list-item link :href="`#/?room=${$root.room}`">
                    <v-list-item-action>
                        <v-icon>{{mdiContentPaste}}</v-icon>
                    </v-list-item-action>
                    <v-list-item-content>
                        <v-list-item-title>{{ $t('clipboard') }}</v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
                <v-list-item link href="#/device">
                    <v-list-item-action>
                        <v-icon>{{mdiDevices}}</v-icon>
                    </v-list-item-action>
                    <v-list-item-content>
                        <v-list-item-title>{{ $t('deviceList') }}</v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
                <v-menu
                    offset-x
                    transition="slide-x-transition"
                    open-on-click
                    open-on-hover
                    :close-on-content-click="false"
                >
                    <template v-slot:activator="{on}">
                        <v-list-item link v-on="on">
                            <v-list-item-action>
                                <v-icon>{{mdiBrightness4}}</v-icon>
                            </v-list-item-action>
                            <v-list-item-content>
                                <v-list-item-title>{{ $t('darkMode') }}</v-list-item-title>
                            </v-list-item-content>
                        </v-list-item>
                    </template>
                    <v-list two-line>
                        <v-list-item-group v-model="$root.dark" color="primary" mandatory>
                            <v-list-item link value="time">
                                <v-list-item-content>
                                    <v-list-item-title>{{ $t('switchByTime') }}</v-list-item-title>
                                    <v-list-item-subtitle>{{ $t('timeRange') }}</v-list-item-subtitle>
                                </v-list-item-content>
                            </v-list-item>
                            <v-list-item link value="prefer">
                                <v-list-item-content>
                                    <v-list-item-title>{{ $t('switchBySystem') }}</v-list-item-title>
                                    <v-list-item-subtitle>{{ $t('usePrefersColorScheme') }}</v-list-item-subtitle>
                                </v-list-item-content>
                            </v-list-item>
                            <v-list-item link value="enable">
                                <v-list-item-content>
                                    <v-list-item-title>{{ $t('keepEnabled') }}</v-list-item-title>
                                </v-list-item-content>
                            </v-list-item>
                            <v-list-item link value="disable">
                                <v-list-item-content>
                                    <v-list-item-title>{{ $t('keepDisabled') }}</v-list-item-title>
                                </v-list-item-content>
                            </v-list-item>
                        </v-list-item-group>
                    </v-list>
                </v-menu>

                <!-- customize primary color -->
                <v-list-item link @click="colorDialog = true; drawer=false;">
                    <v-list-item-action>
                        <v-icon>{{mdiPalette}}</v-icon>
                    </v-list-item-action>
                    <v-list-item-content>
                        <v-list-item-title>{{ $t('changePrimaryColor') }}</v-list-item-title>
                    </v-list-item-content>
                </v-list-item>

                <v-menu
                    offset-x
                    transition="slide-x-transition"
                    open-on-click
                    open-on-hover
                    :close-on-content-click="false"
                >
                    <template v-slot:activator="{ on }">
                        <v-list-item link v-on="on">
                            <v-list-item-action>
                                <v-icon>{{ mdiTranslate }}</v-icon>
                            </v-list-item-action>
                            <v-list-item-content>
                                <v-list-item-title>{{ $t('language') }}</v-list-item-title>
                            </v-list-item-content>
                        </v-list-item>
                    </template>
                    <v-list two-line>
                        <v-list-item-group v-model="$root.language" color="primary" mandatory>
                            <v-list-item link value="browser">
                                <v-list-item-content>
                                    <v-list-item-title>{{ $t('switchByNavigator') }}</v-list-item-title>
                                    <v-list-item-subtitle>{{ $t('useNavigatorLanguage') }}</v-list-item-subtitle>
                                </v-list-item-content>
                            </v-list-item>
                            <v-list-item link value="zh-CN">
                                <v-list-item-content>
                                    <v-list-item-title>简体中文</v-list-item-title>
                                </v-list-item-content>
                            </v-list-item>
                            <v-list-item link value="en">
                                <v-list-item-content>
                                    <v-list-item-title>English</v-list-item-title>
                                </v-list-item-content>
                            </v-list-item>
                        </v-list-item-group>
                    </v-list>
                </v-menu>

                <v-list-item link href="#/about">
                    <v-list-item-action>
                        <v-icon>{{mdiInformation}}</v-icon>
                    </v-list-item-action>
                    <v-list-item-content>
                        <v-list-item-title>{{ $t('about') }}</v-list-item-title>
                    </v-list-item-content>
                </v-list-item>
            </v-list>
        </v-navigation-drawer>

        <v-app-bar
            app
            color="primary"
            dark
        >
            <v-app-bar-nav-icon @click.stop="drawer = !drawer" />
            <v-toolbar-title>{{ $t('cloudClipboard') }}<span class="d-none d-sm-inline" v-if="$root.room">（{{ $t('room') }}：<abbr title="{{ $t('clickToCopy') }}" style="cursor:pointer" @click="navigator.clipboard.writeText($root.room).then(() => $toast(`${$t('roomNameCopied')}: ${$root.room}`).catch(err => $toast.error(`${$t('copyFailed')}: ${err}`)))">{{$root.room}}</abbr>）</span></v-toolbar-title>
            <v-spacer></v-spacer>
            <v-tooltip left>
                <template v-slot:activator="{ on }">
                    <v-btn icon v-on="on" @click="$root.roomInput = $root.room; $root.roomDialog = true">
                        <v-icon>{{mdiBulletinBoard}}</v-icon>
                    </v-btn>
                </template>
                <span>{{ $t('enterRoom') }}</span>
            </v-tooltip>
            <v-tooltip left>
                <template v-slot:activator="{ on }">
                    <v-btn icon v-on="on" @click="if (!$root.websocket && !$root.websocketConnecting) {$root.retry = 0; $root.connect();}">
                        <v-icon v-if="$root.websocket">{{mdiLanConnect}}</v-icon>
                        <v-icon v-else-if="$root.websocketConnecting">{{mdiLanPending}}</v-icon>
                        <v-icon v-else>{{mdiLanDisconnect}}</v-icon>
                    </v-btn>
                </template>
                <span v-if="$root.websocket">{{ $t('connected') }}</span>
                <span v-else-if="$root.websocketConnecting">{{ $t('connecting') }}</span>
                <span v-else>{{ $t('notConnected') }}</span>
            </v-tooltip>
        </v-app-bar>

        <v-main>
            <template v-if="$route.meta.keepAlive">
                <keep-alive><router-view /></keep-alive>
            </template>
            <router-view v-else />
        </v-main>

        <v-dialog v-model="colorDialog" max-width="300" hide-overlay>
            <v-card>
                <v-card-title>{{  $t('pickPrimaryColor') }}</v-card-title>
                <v-card-text>
                    <!--
                    <v-color-picker v-model=" $vuetify.theme.dark? $vuetify.theme.themes.dark.primary: $vuetify.theme.themes.light.primary" hide-inputs></v-color-picker>
                     -->

                    <v-color-picker v-if="$vuetify.theme.dark" v-model=" $vuetify.theme.themes.dark.primary " show-swatches hide-inputs></v-color-picker>
                    <v-color-picker v-else                     v-model=" $vuetify.theme.themes.light.primary" show-swatches hide-inputs></v-color-picker>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="primary" text @click="colorDialog = false">{{ $t('pickOK') }}</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <v-dialog v-model="$root.authCodeDialog" persistent max-width="360">
            <v-card>
                <v-card-title class="headline">{{ $t('needAuthentication') }}</v-card-title>
                <v-card-text>
                    <p>{{ $t('clipboardServiceNotPublic') }}</p>
                    <v-text-field v-model="$root.authCode" :label="$t('password')"></v-text-field>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn
                        color="primary darken-1"
                        text
                        @click="
                            $root.authCodeDialog = false;
                            $root.connect();
                        "
                    >{{ $t('submit') }}</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <v-dialog v-model="$root.roomDialog" persistent max-width="360">
            <v-card>
                <v-card-title class="headline">{{ $t('clipboardRoom') }}</v-card-title>
                <v-card-text>
                    <p>{{ $t('enterRoomName') }}</p>
                    <p>{{ $t('roomVisibility') }}</p>
                    <v-text-field
                        v-model="$root.roomInput"
                        :label="$t('roomName')"
                        :append-icon="mdiDiceMultiple"
                        @click:append="$root.roomInput = ['reimu', 'marisa', 'rumia', 'cirno', 'meiling', 'patchouli', 'sakuya', 'remilia', 'flandre', 'letty', 'chen', 'lyrica', 'lunasa', 'merlin', 'youmu', 'yuyuko', 'ran', 'yukari', 'suika', 'mystia', 'keine', 'tewi', 'reisen', 'eirin', 'kaguya', 'mokou'][Math.floor(Math.random() * 26)] + '-' + Math.random().toString(16).substring(2, 6)"
                    ></v-text-field>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn
                        color="primary darken-1"
                        text
                        @click="$root.roomDialog = false"
                    >{{ $t('cancel') }}</v-btn>
                    <v-btn
                        color="primary darken-1"
                        text
                        @click="
                            $router.push({ path: '/', query: { room: $root.roomInput }});
                            $root.roomDialog = false;
                        "
                    >{{ $t('enterRoom') }}</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </v-app>
</template>

<!-- will filter by data-v-xxx -->
<style scoped>
.v-navigation-drawer >>> .v-navigation-drawer__border {
    pointer-events: none;
}
</style>

<!-- not filter by data-v-xxx -->
<style>
/* global style */
.v-snack.v-snack--bottom {
    bottom: 30%;
}
</style>

<script>
import {
    mdiContentPaste,
    mdiDevices,
    mdiInformation,
    mdiLanConnect,
    mdiLanDisconnect,
    mdiLanPending,
    mdiTranslate,
    mdiBrightness4,
    mdiBulletinBoard,
    mdiDiceMultiple,
    mdiPalette,
} from '@mdi/js';

export default {
    data() {
        return {
            drawer: false,
            colorDialog: false,
            mdiContentPaste,
            mdiDevices,
            mdiInformation,
            mdiLanConnect,
            mdiLanDisconnect,
            mdiLanPending,
            mdiTranslate,
            mdiBrightness4,
            mdiBulletinBoard,
            mdiDiceMultiple,
            mdiPalette,
            navigator,
        };
    },
    mounted() { // primary color <==> localStorage

        // theme colors <== localStorage
        const darkPrimary = localStorage.getItem('darkPrimary');
        const lightPrimary = localStorage.getItem('lightPrimary');
        if (darkPrimary) {
            this.$vuetify.theme.themes.dark.primary = darkPrimary;
        }
        if (lightPrimary) {
            this.$vuetify.theme.themes.light.primary = lightPrimary;
        }

        // theme colors ==> localStorage
        this.$watch('$vuetify.theme.themes.dark.primary', (newVal) => {
            localStorage.setItem('darkPrimary', newVal);
        });
        this.$watch('$vuetify.theme.themes.light.primary', (newVal) => {
            localStorage.setItem('lightPrimary', newVal);
        });
    },
};


</script>
