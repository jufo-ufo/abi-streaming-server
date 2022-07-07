<script lang="ts">
import InformationPannel from "./InformationPannel.svelte";

export let information = {
    name: "",
    id: 0,
    memory: 0,
    swap: 0,
    cores: 0,
    addresses: [],
    disks: []
}

</script>

<main>
    <InformationPannel {...information}/>
    <div class="terminal">
        [Terminal]
    </div>
</main>

<style lang="scss">
    @use "../global.scss" as global;

main {
    @include global.card();
    grid-row: span 3 / auto;
    padding: 0;
};

.terminal {
    height: calc(50% - global.$card_padding*2);
    padding: global.$card_padding;
    background-color: #1f1f1f;
    border-radius: 0 0 15px 15px;
    color: white;
}

</style>