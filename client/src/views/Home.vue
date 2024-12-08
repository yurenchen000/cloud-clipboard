<template>
    <v-container>
        <v-row>
            <!-- send panel //wide screen -->
            <v-col cols="12" md="4" class="hidden-sm-and-down">
                <send-text></send-text>
                <v-divider class="my-4"></v-divider>
                <send-file></send-file>
            </v-col>
            <!-- msg list -->
            <v-col cols="12" md="8">
                <v-fade-transition group>
                    <div :is="`received-${item.type}`" v-for="item in $root.received" :key="item.id" :meta="item"></div>
                </v-fade-transition>
                <div class="text-center caption text--secondary py-2">{{ $root.received.length ? $t('endOfList') : $t('emptyList') }}</div>
            </v-col>
        </v-row>

        <!-- float btn //narrow screen -->
        <!-- 
        <v-speed-dial
            v-model="fab"
            bottom
            right
            fixed
            direction="top"
            transition="scale-transition"
            class="hidden-md-and-up"
            style="transform:translateY(-64px)"
        >
            <template v-slot:activator>
                <v-btn
                    v-model="fab"
                    fab
                    dark
                    color="primary"
                >
                    <v-icon>{{mdiPlus}}</v-icon>
                </v-btn>
            </template>
            <v-btn fab dark small color="primary" @click="dialog = true; mode = 'file'; setTimeout(() => $refs.dialogFile.focus(), 300)">
                <v-icon>{{mdiFileDocumentOutline}}</v-icon>
            </v-btn>
            <v-btn fab dark small color="primary" @click="dialog = true; mode = 'text'; setTimeout(() => $refs.dialogText.focus(), 300)">
                <v-icon>{{mdiText}}</v-icon>
            </v-btn>
        </v-speed-dial>
        -->

        <!--  float single  -->
        <v-speed-dial
            v-model="fab"
            bottom
            right
            fixed
            direction="top"
            transition="scale-transition"
            class="hidden-md-and-up"
            style="transform:translateY(-64px)"
        >
            <template v-slot:activator>
                <v-btn @click="mode||='text'; dialog = true; focusDialog()"
                    v-model="fab"
                    fab
                    dark
                    color="primary"
                >
                    <v-icon>{{mdiPlus}}</v-icon>
                </v-btn>
            </template>
        </v-speed-dial>

        <!-- send dialog //narrow screen -->
        <!-- 
            transition="dialog-top-transition"
            
            max-width="100%"
            class="h-auto"
            dialog-margin="0"
            fullscreen
            width="100%" 
            hide-overlay
        -->
        <v-dialog
            v-model="dialog"
            :content-class="['chen_bottom', fullDialog?'chen_full':''].join(' ')"
            transition="dialog-bottom-transition"
            scrollable
        >
            <v-card>
                <!-- title -->
                <v-toolbar dark dense color="primary" class="flex-grow-0">
                    <v-btn icon @click="dialog = false">
                        <v-icon>{{mdiClose}}</v-icon>
                    </v-btn>
                    <v-toolbar-title v-if="mode === 'text'">{{ $t('sendText') }}</v-toolbar-title>
                    <v-toolbar-title v-if="mode === 'file'">{{ $t('sendFile') }}</v-toolbar-title>
                    <v-spacer></v-spacer>

                    <v-tooltip left>
                        <template v-slot:activator="{ on }">
                            <v-btn icon v-on="on" @click="fullDialog=!fullDialog;" >
                                <!-- 
                                <v-icon >{{mdiFullscreen}}</v-icon>
                                <v-icon v-if="!fullDialog">{{mdiArrowCollapseUp}}</v-icon>
                                <v-icon v-if=" fullDialog">{{mdiArrowExpandDown}}</v-icon>
                                 -->
                                <v-icon v-if="!fullDialog">{{mdiChevronDoubleUp}}</v-icon>
                                <v-icon v-if=" fullDialog">{{mdiChevronDoubleDown}}</v-icon>
                            </v-btn>
                        </template>
                        <span v-if="!fullDialog">fullscreen</span>
                        <span v-if=" fullDialog">dialog</span>
                    </v-tooltip>

                    <v-tooltip left>
                        <template v-slot:activator="{ on }">
                            <v-btn icon v-on="on" @click="mode = mode === 'text' ? 'file' : 'text'; focusDialog()" >
                                <v-icon v-if="mode === 'file'">{{mdiText}}</v-icon>
                                <v-icon v-if="mode === 'text'">{{mdiFileDocumentOutline}}</v-icon>
                            </v-btn>
                        </template>
                        <span v-if="mode === 'file'">{{ $t('sendText') }}</span>
                        <span v-if="mode === 'text'">{{ $t('sendFile') }}</span>
                    </v-tooltip>
                </v-toolbar>
                <!-- content -->
                <!-- 
                class="my-4"
                 -->
                <v-card-text class="px-4">
                    <div class="mt-4">
                        <send-text ref="dialogText" v-if="mode === 'text'"></send-text>
                        <send-file ref="dialogFile" v-if="mode === 'file'"></send-file>
                    </div>
                </v-card-text>
            </v-card>
        </v-dialog>
    </v-container>
</template>


<style scoped>

/* 
//---- work
.v-dialog__content >>> .v-dialog { 
>>> .v-dialog { 
//----- not work
.v-dialog {  
v-dialog >>> .v-dialog {
*/

>>> .v-dialog {
  margin: 0 !important;
  color: red;
}
>>> .v-dialog.chen_bottom {
    position: fixed;
    bottom: 0;
}
>>> .v-dialog.chen_full {
    height: 100%;
    max-height: unset;
}

</style>

<script>
import SendText from '@/components/SendText.vue';
import SendFile from '@/components/SendFile.vue';
import ReceivedText from '@/components/received-item/Text.vue';
import ReceivedFile from '@/components/received-item/File.vue';
import {
    mdiPlus,
    mdiFileDocumentOutline,
    mdiText,
    mdiClose,
    mdiFullscreen,
    mdiArrowExpandUp,
    mdiArrowCollapseDown,
    mdiArrowCollapseUp,
    mdiArrowExpandDown,
    mdiChevronDoubleUp,
    mdiChevronDoubleDown,
    mdiSend,
} from '@mdi/js';

export default {
    components: {
        SendText,
        SendFile,
        ReceivedText,
        ReceivedFile,
    },
    data() {
        return {
            fab: false,
            dialog: false,
            mode: null,
            fullDialog: false,
            mdiPlus,
            mdiFileDocumentOutline,
            mdiText,
            mdiClose,
            mdiFullscreen,
            mdiArrowExpandUp,
            mdiArrowCollapseDown,
            mdiArrowCollapseUp,
            mdiArrowExpandDown,
            mdiChevronDoubleUp,
            mdiChevronDoubleDown,
            mdiSend,
        };
    },
    methods: {
        closeDialog() {
            this.dialog = false;
        },
        setTimeout(f, t) {
            return setTimeout(f, t);
        },
        focusDialog(){
            switch (this.mode) {
                case 'text': setTimeout(() => this.$refs.dialogText.focus(), 300); break;
                case 'file': setTimeout(() => this.$refs.dialogFile.focus(), 300); break;
            }
        },
    },
    watch: {
        dialog(newval) {
            if (newval) {
                history.pushState(null, null, location.href);
                addEventListener('popstate', this.closeDialog);
            } else {
                removeEventListener('popstate', this.closeDialog);
            }
        },
    },
}
</script>
