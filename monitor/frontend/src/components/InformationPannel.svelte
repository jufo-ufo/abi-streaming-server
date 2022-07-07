<script lang="ts">
    function format_metric(value: number, unit: string): string {
        const metric_units = ["Y", "Z", "E", "P", "T", "G", "M", "k", " ", "m", "μ", "n", "p", "f", "a", "z", "y"];
        let v = value;
        let i = 0;

        if(v == 0) {
            let v_string = v.toString();
            return v_string + "  " + unit;
        }

        for(; i<metric_units.length; i++) {
            if(v / Math.pow(1000, 8-i) > 1) {
                let v_string = (v/Math.pow(1000, 8-i)).toFixed(2);
                return v_string + " " + metric_units[i] + unit;
            }
        }

        let v_string = (v/Math.pow(1000, -8)).toFixed(2);
        return v_string + " " + metric_units[metric_units.length-1] + unit;
    }

    interface network_info {
        ipv6: string,
        ipv4: string,
        name: string
    };


    interface disk_info {
        format: string,
        size: number,
        name: string,
        mount: string
    };

    export let name: string;
    export let id: number;
    export let memory: number;
    export let swap: number;
    export let cores: number;
    export let addresses: Array<network_info>;
    export let disks: Array<disk_info>;


</script>

<main>
    <h2>Probe Information</h2>
    <div class="info-table">
        <p><b>Name</b></p> <p>{name}</p>
        <p><b>ID</b></p> <p>{id}</p>

        <p style="height: 1em;"></p> <p></p>

        <p><b>Memory</b></p> <p>{format_metric(memory, "B")}</p>
        <p><b>Swap</b></p> <p>{format_metric(swap, "B")}</p>
        <p><b>CPU Cores</b></p> <p>{cores}</p>

        <p style="height: 1em;"></p> <p></p>

        {#each addresses as address, i}
            <p>
                {#if i == 0}<b>Addresses</b>{/if}
            </p> 
            <div class="sub-table">
                <p>{address.name}</p> <p>{address.ipv4}</p> <p></p>
            </div>
        {/each}

        <p style="height: 1em;"></p> <p></p>

        {#each disks as disk, i}
            <p>
                {#if i==0}<b>Disks</b>{/if}
            </p> 
            <div class="sub-table">
                <p>{disk.name}</p> <p>{format_metric(disk.size, "B")}</p> <p>{disk.mount} ({disk.format})</p>
            </div>
        {/each}

        <p style="height: 1em;"></p> <p></p> 

        <p><b>GPU</b></p> <p>no idea</p>

    </div>
</main>

<style lang="scss">
    @use "../global.scss" as global;

main {
    @include global.card();
    height: calc(50%  - global.$card_padding*2);
    padding: global.$card_padding;
};

.info-table {
    display: grid;
    grid-template-columns: 1fr 5fr;
    margin-top: 15px;
}

.info-table > * {
    margin: 0;
    margin-bottom: 2px;
    color: black;
}

//.info-table > *:nth-child(2n-1) {
//    
//}

.sub-table {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
}

.sub-table > * {
    padding: 0;
    margin: 0;
}
</style>