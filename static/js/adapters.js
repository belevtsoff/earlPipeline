App.ApplicationAdapter = DS.RESTAdapter.extend({
    // prepend paths for 'units' and 'edges' with current pipeline id
    pathForType: function (type) {
        if (type == 'unit' || type == 'edge') {
            var path = this._super("pipeline") + "/" +
                App.get("currentPipeline.id") + "/" +
                this._super(type);

            return path;
        }
        else {
            return this._super(type);
        }
    },

    namespace: App.get('namespace'),
})
