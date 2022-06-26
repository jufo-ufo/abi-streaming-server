
<style lang="scss">
    @use "styles/global";
    
    div {
		@include global.card;	
        grid-row: span 2 /auto;
    }

    h1 {
        margin: 0;
    }
</style>

<div>
    <h1>Server Info</h1>
</div>