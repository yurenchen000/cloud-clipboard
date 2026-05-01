<template>
    <v-container fill-height>
        <v-row justify="center" align="center" class="pa-3">
            <div class="text-center">
                <div class="headline my-4">Cloud Clipboard {{$root.config.version}}</div>
                {{ $t('aboutDescription1') }}
                <br>
                {{ $t('aboutDescription2') }}
                <br>
               
                <br>
                
            <pre style="text-align: left;">
                nodejs version: <a href="https://github.com/TransparentLC/cloud-clipboard" target="_blank">GitHub</a>

                ----
                go, py version: <a href="https://github.com/yurenchen000/cloud-clipboard" target="_blank">Github</a>

                - server: golang, python version 
                // go version with bundled frontend, only 9MB

                - client: experience optimized version
            </pre>

            </div>
        </v-row>
    </v-container>
</template>

<script>
export default {

}
</script>
