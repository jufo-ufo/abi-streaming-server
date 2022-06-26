
<script lang="ts">
    import Chart from 'chart.js/auto';
	let chartData;
	import { onMount } from 'svelte';

	export let titel: string = "Untitle Plot";

	let chartValues = [20, 10, 5, 2, 20, 30, 45];
	let chartLabels = ['January', 'February', 'March', 'April', 'May', 'June', 'July'];
	let ctx;
	let chartCanvas;

	onMount(async () => {
		ctx = chartCanvas.getContext('2d');
			var chart = new Chart(ctx, {
				type: 'line',
				data: {
					labels: chartLabels,
					datasets: [{
							label: 'Revenue',
							backgroundColor: 'rgb(255, 99, 132)',
							borderColor: 'rgb(255, 99, 132)',
							data: chartValues
					}]
				}
		});

	});
</script>

<style lang="scss">
	@use "styles/global";
	
	div {
		@include global.card;	
	}

	h1 {
        font-size: 24px;
        margin: 0;
    }
</style>

<div class="card">
    <h1>{titel}</h1>
    <canvas bind:this={chartCanvas} id="myChart"></canvas>
</div>