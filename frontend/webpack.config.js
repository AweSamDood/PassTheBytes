module.exports = {
    // other configurations...
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules\/@antv\/util/,
                use: ['source-map-loader'],
                enforce: 'pre'
            }
        ]
    }
};