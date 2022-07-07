<script lang="ts">
import PlotCard from "./PlotCard.svelte";
import ServerInfoCard from "./ServerInfoCard.svelte";

import { onMount } from 'svelte';
import { prop_dev } from "svelte/internal";

export let probe_id: number = 0;

let information = {
    name: "Feuerlöscher PC",
    id: 42,
    memory: 16000000000,
    swap: 2000000000,
    cores: 4,
    addresses: [
        {ipv6: "2001:0db8:85a3:0000:0000:8a2e:0370:7334", ipv4: "192.168.113.99", name: "esp0"},
        {ipv6: "2001:0db8:85a3:0000:0000:8a2e:0370:7334", ipv4: "127.0.0.1", name: "lo"}
    ],
    disks: [
        {format: "ext4", size: 1000000000000, name: "/dev/sda1", mount: "/"},
        {format: "vfat", size: 16000000000, name: "/dev/sdb1", mount: "/boot"},
    ]
}

onMount(async () => {
    const res = await fetch(`http://localhost:5000/probe/${probe_id}/info`);
    if(res.ok) {
        information = await res.json();
    } else {
        console.log("Falid fetching probe information!");
    }
});

</script>

<div class="main">
    <PlotCard />
    <PlotCard />
    <ServerInfoCard {information}/>
    <PlotCard />
    <PlotCard />
    <PlotCard />
    <PlotCard />
</div>

<style lang="scss">
    .main {
        height: calc(100% - 20px);
        width : calc(100% - 20px);

        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        padding: 10px;
    }

</style>