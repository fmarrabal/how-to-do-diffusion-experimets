/* Same numerical engine in browser and the offline WPF WebView. */
importScripts('spatial-encoding.js');
self.onmessage = function(event) {
  try {
    const {mode,parameters} = event.data;
    if (!['simulate','convergence'].includes(mode)) throw new Error('Unknown spatial calculation');
    self.postMessage({ok:true,result:AcademySpatialEncoding[mode](parameters)});
  } catch(error) { self.postMessage({ok:false,error:String(error.message||error)}); }
};
