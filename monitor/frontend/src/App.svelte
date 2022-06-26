<script lang="ts">
    import TimeSeriesPlotCard from "./TimeSeriesPlotCard.svelte";
    import ServerInfoCard from "./ServerInfoCard.svelte";
</script>

<style lang="css">
main {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(3, 1fr);
    gap: 1rem;

    height: 100%;
    width: 100%;
}
</style>

<main>
    <TimeSeriesPlotCard titel="CPU"/>
    <TimeSeriesPlotCard titel="Network"/>
    <ServerInfoCard/>
    <TimeSeriesPlotCard titel="Memory/Swap"/>
    <TimeSeriesPlotCard titel="Bandwidth"/>
    <TimeSeriesPlotCard titel="Client Count/Acceped"/>
    <TimeSeriesPlotCard titel="Disk"/>
    <TimeSeriesPlotCard titel="Core Temperatur"/>
</main>
