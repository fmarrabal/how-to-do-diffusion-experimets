using System.Diagnostics;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using DiffAtOnce.Academy.Tutor;

if (args.Length < 5) throw new ArgumentException("Usage: NativeResearchCheck KNOWLEDGE MODEL_DIRECTORY COURSE OUTPUT_JSON fallback|native");
var knowledgePath=Path.GetFullPath(args[0]);var modelPath=Path.GetFullPath(args[1]);var coursePath=Path.GetFullPath(args[2]);var output=Path.GetFullPath(args[3]);var mode=args[4];
if(mode is not ("fallback" or "native"))throw new ArgumentException("Unknown probe mode.");
if(File.Exists(output))throw new IOException("Preserve completed native probe instead of overwriting it.");
var checks=new List<object>();var allPassed=true;var timer=Stopwatch.StartNew();
void Add(string id,bool passed,object? detail=null){checks.Add(new{id,passed,detail});allPassed&=passed;Console.WriteLine(id+": "+(passed?"PASS":"FAIL"));}
string Hash(string path)=>Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();
string Normal(string value)=>string.Concat(value.Normalize(NormalizationForm.FormD).Where(c=>CharUnicodeInfo.GetUnicodeCategory(c)!=UnicodeCategory.NonSpacingMark)).ToLowerInvariant();
bool NumericMatch(string value,string expected)
{
    if(expected.Length==0)return true;
    var pieces=expected.Split('=');var match=Regex.Match(value,Regex.Escape(pieces[0])+@"\s*[=:]\s*([-+]?[0-9]+(?:[.,][0-9]+)?(?:[eE][-+]?[0-9]+)?)",RegexOptions.IgnoreCase|RegexOptions.CultureInvariant);
    return match.Success&&double.TryParse(match.Groups[1].Value.Replace(',','.'),NumberStyles.Float,CultureInfo.InvariantCulture,out var actual)&&double.TryParse(pieces[1],NumberStyles.Float,CultureInfo.InvariantCulture,out var reference)&&Math.Abs(actual-reference)<=Math.Max(1e-7,Math.Abs(reference)*1e-6);
}
bool NativeMechanism(string answer,string context)
{
    using var document=JsonDocument.Parse(context);if(!document.RootElement.TryGetProperty("calculation_context",out var trace))return true;
    var value=Normal(answer);var formula=trace.GetProperty("calculation").GetString();var unit=trace.GetProperty("unit").GetString();
    var units=unit=="us"?Regex.IsMatch(answer,@"(?<![A-Za-z])(?:us|µs|μs)(?![A-Za-z])"):Regex.IsMatch(answer,@"\bfactor\b");
    if(!units)return false;
    if(formula=="P90=P180/2")return (value.Contains("angle")||value.Contains("angulo"))&&value.Contains("propor")&&(value.Contains("duration")||value.Contains("duracion"))&&value.Contains("180")&&(value.Contains("power")||value.Contains("potencia"))&&(value.Contains("maximum")||value.Contains("maximo")||value.Contains("polarity")||value.Contains("polaridad"));
    if(formula=="P90=P360/4")return value.Contains("360")&&new[]{"four","quarter","/4","cuatro","cuarto"}.Any(value.Contains)&&(value.Contains("power")||value.Contains("potencia"));
    if(formula=="b_scale=gradient_scale^2")return Regex.IsMatch(value,@"\bq\b")&&Regex.IsMatch(value,@"\bb\b")&&value.Contains("line")&&value.Contains("integr")&&(value.Contains("waveform")||value.Contains("forma"))&&(value.Contains("timing")||value.Contains("tiempo")||value.Contains("delta"));
    if(formula=="D_ratio=gradient_scale^2")return value.Contains("d_nominal")&&value.Contains("d_reference")&&(value.Contains("ratio")||value.Contains("cociente"))&&(value.Contains("shared")||value.Contains("compart")||value.Contains("comun"))&&(value.Contains("bias")||value.Contains("sesgo"));
    if(formula=="noise_ratio=1/sqrt(replicates)")return value.Contains("independ")&&value.Contains("sqrt")&&(value.Contains("shared")||value.Contains("common"))&&value.Contains("bias")&&(value.Contains("remains")||value.Contains("does not remove"));
    return false;
}
GuardControls.Run(Add);
using var knowledge=JsonDocument.Parse(File.ReadAllText(knowledgePath));
var legacyManifestType=typeof(TutorService).GetNestedType("TutorManifest",System.Reflection.BindingFlags.NonPublic)!;
var absentResearchFlag=JsonSerializer.Deserialize("{}",legacyManifestType)!;
Add("legacy_manifest_absent_research_flag_stays_false",legacyManifestType.GetProperty("ResearchQualityPassed")!.GetValue(absentResearchFlag) is false);
var preservedQuestion="Identified180 crossing at18 us; how do I check polarity and avoid mistaking360 degrees?";
var legacyTrace=new{calculation="P90 = P180 / 2",inputs=new{p180_us=18},result=9,assumptions=new[]{"Identified180 crossing","Unchanged RF power"}};
Add("contradictory_legacy_pulse_not_canonicalized",!ResearchTutorService.TryLegacyNumericPrompt("en",preservedQuestion,"pulse-calibration",legacyTrace,Array.Empty<object>(),out _,out _));
var ordinaryQuestion="Identified 180 crossing at 18 us; explain 90 degrees and the polarity check.";
var compatible=ResearchTutorService.TryLegacyNumericPrompt("en",ordinaryQuestion,"pulse-calibration",legacyTrace,Array.Empty<object>(),out _,out var compatiblePayload);
using(var compatibleDoc=JsonDocument.Parse(compatiblePayload))Add("typed_compatibility_preserves_original_subquestion_and_assumptions",compatible&&compatibleDoc.RootElement.GetProperty("original_question").GetString()==ordinaryQuestion&&compatibleDoc.RootElement.GetProperty("calculation_context").GetProperty("assumptions").GetArrayLength()==2&&!compatibleDoc.RootElement.GetProperty("question").GetString()!.Contains("first",StringComparison.OrdinalIgnoreCase));
var topics=knowledge.RootElement.GetProperty("chunks").EnumerateArray().Select(c=>c.GetProperty("id").GetString()!).ToArray();
await using(var documentary=new ResearchTutorService(knowledgePath,Path.Combine(Path.GetDirectoryName(output)!,"nonexistent-model-read-only-probe")))
{
    foreach(var topic in topics)Add("sources_"+topic,documentary.GetTopicSources(topic).Count>0);
    foreach(var lang in new[]{"es","en"})
    {
        var a=await documentary.AskAsync(lang,"Explain the stated evidence.","uncertainty",null,CancellationToken.None,hintLevel:0);
        var b=await documentary.AskAsync(lang,"Explain the stated evidence.","uncertainty",null,CancellationToken.None,hintLevel:1);
        var c=await documentary.AskAsync(lang,"Explain the stated evidence.","uncertainty",null,CancellationToken.None,hintLevel:2);
        Add("progressive_hints_"+lang,!a.IsModelAnswer&&!b.IsModelAnswer&&!c.IsModelAnswer&&a.Text!=c.Text&&a.GeneratedText is null&&c.Sources.Count>0,new{a,b,c});
    }
    var unknown=await documentary.AskAsync("en","Question","unknown-topic",null,CancellationToken.None);
    Add("unknown_topic_honest",!unknown.IsModelAnswer&&unknown.Sources.Count==0&&unknown.Status=="research_topic_unknown",unknown);
    using var cancelled=new CancellationTokenSource();cancelled.Cancel();
    try{await documentary.AskAsync("en","Question","uncertainty",null,cancelled.Token);Add("pre_cancelled",false);}catch(OperationCanceledException){Add("pre_cancelled",true);}
    try{await documentary.AskAsync("en","Question","uncertainty","not-json",CancellationToken.None);Add("invalid_context",false);}catch(JsonException){Add("invalid_context",true);}
    try{await documentary.AskAsync("en","Question","uncertainty","{\"case\":{\"hiddenTruth\":{\"D\":1}}}",CancellationToken.None);Add("hidden_truth_not_supplied_to_student",false);}catch(ArgumentException){Add("hidden_truth_not_supplied_to_student",true);}
    var conflict=await documentary.AskAsync("en","This may be360 degrees: should I divide the180 context by two?","calibration",JsonSerializer.Serialize(new{calculation_context=legacyTrace}),CancellationToken.None);
    Add("contradictory_research_pulse_explains_boundary",!conflict.IsModelAnswer&&conflict.GeneratedText is null&&conflict.Status=="contradictory_pulse_context"&&conflict.Text.Contains("Identify the crossing",StringComparison.Ordinal),conflict);
}
var researchPassed=true;var originalPassed=true;
if(mode=="native")
{
    await using var research=new ResearchTutorService(knowledgePath,modelPath,allowPendingNativeEvaluation:true);
    var cases=new[]{
        (Language:"es",Topic:"calibration",Question:"Cruce de 180° identificado a 74 us, potencia fija. Explica el resultado P90 del contexto y su causa física.",Context:JsonSerializer.Serialize(new{calculation_context=new{kind="synthetic-worked-example",calculation="P90=P180/2",inputs=new{p180_us=74},result=37,result_label="P90",unit="us",experimental_calibration=false}}),Numeric:"P90=37"),
        (Language:"en",Topic:"calibration",Question:"The entire effective gradient waveform scales by 0.62, with unchanged timings. Explain b_scale and the physical reason.",Context:JsonSerializer.Serialize(new{calculation_context=new{kind="synthetic-worked-example",calculation="b_scale=gradient_scale^2",inputs=new{gradient_scale=.62},result=.3844,result_label="b_scale",unit="factor",experimental_calibration=false}}),Numeric:"b_scale=0.3844"),
        (Language:"es",Topic:"uncertainty",Question:"g_real/g_nominal=0.935; misma forma completa. Explica D_nominal/D_reference del contexto y qué ocurre al repetir.",Context:JsonSerializer.Serialize(new{calculation_context=new{kind="synthetic-worked-example",calculation="D_ratio=gradient_scale^2",inputs=new{gradient_scale=.935},result=.874225,result_label="D_ratio",unit="factor",experimental_calibration=false}}),Numeric:"D_ratio=0.874225"),
        (Language:"en",Topic:"uncertainty",Question:"Average 196 replicates with independent noise and identical calibration. Explain noise_ratio and shared bias.",Context:JsonSerializer.Serialize(new{calculation_context=new{kind="synthetic-worked-example",calculation="noise_ratio=1/sqrt(replicates)",inputs=new{replicates=196},result=1.0/14,result_label="noise_ratio",unit="factor",experimental_calibration=false}}),Numeric:"noise_ratio=0.07142857"),
        (Language:"en",Topic:"calibration",Question:"This null has been identified as a360-degree crossing at 88 us, with unchanged RF power. Explain P90 and why the divisor is four, not two.",Context:JsonSerializer.Serialize(new{calculation_context=new{kind="synthetic-worked-example",calculation="P90=P360/4",inputs=new{p360_us=88},result=22,result_label="P90",unit="us",experimental_calibration=false}}),Numeric:"P90=22"),
        (Language:"es",Topic:"calibration",Question:"Este nulo se ha identificado como cruce de360 grados a 92 us, con potencia RF constante. Explica P90 y por qué el divisor es cuatro, no dos.",Context:JsonSerializer.Serialize(new{calculation_context=new{kind="synthetic-worked-example",calculation="P90=P360/4",inputs=new{p360_us=92},result=23,result_label="P90",unit="us",experimental_calibration=false}}),Numeric:"P90=23"),
        (Language:"es",Topic:"measure-next",Question:"Antes de adquirir el control, ¿qué resultado predice cada hipótesis y qué diferencia sería mayor que el ruido esperado?",Context:"{\"candidateCount\":2,\"evidenceStatus\":\"synthetic-education-only\"}",Numeric:""),
        (Language:"en",Topic:"spatial-diffusion",Question:"Which analytical limit and grid refinement would you check before interpreting a computed profile?",Context:"{\"dimensions\":1,\"evidenceStatus\":\"synthetic-education-only\"}",Numeric:"")
    };
    foreach(var item in cases)
    {
        using var timeout=new CancellationTokenSource(TimeSpan.FromMinutes(4));
        var answer=await research.AskAsync(item.Language,item.Question,item.Topic,item.Context,timeout.Token,new Progress<string>(Console.WriteLine));
        var source=knowledge.RootElement.GetProperty("chunks").EnumerateArray().Single(c=>c.GetProperty("id").GetString()==item.Topic);
        var expected=source.GetProperty("why").GetProperty(item.Language).GetString()+"\n\n"+source.GetProperty("body").GetProperty(item.Language).GetString();
        var numeric=NumericMatch(answer.GeneratedText??"",item.Numeric);
        var causal=NativeMechanism(answer.GeneratedText??"",item.Context);
        var passed=answer.IsModelAnswer&&answer.IncludesCourseQuote&&answer.CourseQuote==expected&&!string.IsNullOrWhiteSpace(answer.GeneratedText)&&answer.GeneratedSources?.Count>0&&numeric&&causal;
        if(item.Question.Contains("360-degree",StringComparison.Ordinal))passed&=(answer.GeneratedText??"").Contains("360",StringComparison.Ordinal)&&new[]{"four","quarter","/4","cuatro","cuarto"}.Any(term=>(answer.GeneratedText??"").Contains(term,StringComparison.OrdinalIgnoreCase));
        researchPassed&=passed;Add("research_native_"+item.Language+"_"+item.Topic+"_"+(item.Numeric.Length>0?item.Numeric.Split('=')[0]:"qualitative")+(item.Question.Contains("360",StringComparison.Ordinal)?"_p360":""),passed,new{input=new{language=item.Language,topic=item.Topic,question=item.Question,context=item.Context},answer});
    }
    using(var cancel=new CancellationTokenSource(TimeSpan.FromMinutes(4)))
    {
        var triggered=false;var latency=Stopwatch.StartNew();
        var progress=new InlineProgress(value=>{if(value.Contains("preparing a sourced",StringComparison.Ordinal)){triggered=true;latency.Restart();cancel.CancelAfter(100);}});
        try{await research.AskAsync("en","Explain the cause and one practical check.","journey",null,cancel.Token,progress);researchPassed=false;Add("research_generation_cancelled",false);}
        catch(OperationCanceledException){var passed=triggered&&latency.Elapsed.TotalSeconds<10;researchPassed&=passed;Add("research_generation_cancelled",passed,new{triggered,seconds=latency.Elapsed.TotalSeconds});}
    }
    // The same single GGUF must retain the original course's actual runtime
    // contract; this is separately labelled exposed regression, not a new test.
    await using var original=new TutorService(coursePath,modelPath,captureEvaluationDiagnostics:true,allowPendingResearchNativeEvaluation:true);
    var oldCases=new[]{
        (Language:"es",Module:"pulse-calibration",Question:"En un ejemplo sintético el mínimo de 180° aparece a 18 µs. ¿Cuánto vale el pulso de 90° y qué debería comprobar?",Number:"9"),
        (Language:"en",Module:"sequence-b",Question:"In an ideal rectangular PGSE example, if I double g and keep delta and Delta unchanged, what happens to b?",Number:"4"),
        (Language:"es",Module:"spen",Question:"¿Qué hay que hacer con las dos polaridades EPSI para reconstruir la frecuencia y la difusión?",Number:""),
        (Language:"en",Module:"time-resolved",Question:"Why does changing fractions during a sequential ramp bias D even when each species has a constant diffusion coefficient?",Number:"")
    };
    foreach(var item in oldCases)
    {
        using var timeout=new CancellationTokenSource(TimeSpan.FromMinutes(4));
        var answer=await original.AskAsync(item.Language,item.Question,item.Module,null,timeout.Token,new Progress<string>(Console.WriteLine));
        var passed=answer.IsModelAnswer&&answer.IncludesCourseQuote&&!string.IsNullOrWhiteSpace(answer.CourseQuote)&&!string.IsNullOrWhiteSpace(answer.GeneratedText)&&answer.Sources.Count>0&&(item.Number.Length==0||answer.GeneratedText.Contains(item.Number,StringComparison.Ordinal));
        var text=answer.Text.ToLowerInvariant();
        if(item.Module=="spen")passed&=(text.Contains("reorden")||text.Contains("indice")||text.Contains("índice"))&&text.Contains("fase")&&(text.Contains("fourier")||text.Contains("dft"));
        if(item.Module=="time-resolved")passed&=(text.Contains("fraction")||text.Contains("concentration")||text.Contains("population"))&&(text.Contains("attenuation")||text.Contains("signal"));
        originalPassed&=passed;Add("original_native_regression_"+item.Language+"_"+item.Module,passed,new{question=item.Question,answer,evaluationDiagnostics=original.LastEvaluationDiagnostics});
    }
    using var derivations=JsonDocument.Parse(File.ReadAllText(Path.Combine(Path.GetDirectoryName(coursePath)!,"derivations.json")));
    foreach(var chapter in derivations.RootElement.GetProperty("chapters").EnumerateArray())
    foreach(var language in new[]{"es","en"})
    {
        var id=chapter.GetProperty("id").GetString()!;
        string Local(JsonElement e,string key)=>e.TryGetProperty(key,out var v)&&v.ValueKind==JsonValueKind.Object&&v.TryGetProperty(language,out var x)?x.GetString()??"":"";
        var expected=string.Join("\n\n",chapter.GetProperty("steps").EnumerateArray().Select(step=>Local(step,"title")+"\n"+step.GetProperty("equationPlain").GetString()+"\n"+Local(step,"explanation")+"\n"+(language=="es"?"Supuestos: ":"Assumptions: ")+Local(step,"assumptions")+(Local(step,"notationNote") is {Length:>0} note?"\n"+(language=="es"?"Nota sobre la impresión original: ":"Original printed notation note: ")+note:"")));
        var answer=await original.AskAsync(language,language=="es"?"Explica la ecuación y sus supuestos.":"Explain the equation and its assumptions.","derivation:"+id,null,CancellationToken.None);
        var expectedSources=chapter.GetProperty("steps").EnumerateArray().SelectMany(s=>s.GetProperty("sourceRefs").EnumerateArray()).Select(s=>s.GetProperty("sourceId").GetString()).Distinct().Order().ToArray();
        var passed=!answer.IsModelAnswer&&answer.GeneratedText is null&&answer.IncludesSupplementalEvidence&&answer.CourseQuote==expected&&answer.Sources.Select(s=>s.Id).Order().SequenceEqual(expectedSources);
        originalPassed&=passed;Add("mathematical_course_documentary_preserved_"+language+"_"+id,passed,new{answer,expectedQuoteSha256=Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(expected))).ToLowerInvariant(),literalPreserved=answer.CourseQuote==expected});
    }
}
var report=new{version="1.3.0",mode,passed=allPassed,nativeModelGateExecuted=mode=="native",nativeResearchPassed=mode=="native"&&researchPassed,nativeOriginalRegressionPassed=mode=="native"&&originalPassed,elapsedSeconds=timer.Elapsed.TotalSeconds,knowledgeSha256=Hash(knowledgePath),courseSha256=Hash(coursePath),systemSha256=Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(ResearchTutorService.SystemInstructions))).ToLowerInvariant(),modelSha256=mode=="native"?Hash(Path.Combine(modelPath,"model.gguf")):null,scope="Actual local C# runtime. Fallback/hints are documentary. Native mode executes the single quantized candidate with actual source/numeric/hybrid guards and exposed original-course regression. No hardware, experimental or learner validation.",checks};
Directory.CreateDirectory(Path.GetDirectoryName(output)!);File.WriteAllText(output,JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true}));
Console.WriteLine(JsonSerializer.Serialize(new{report.passed,report.nativeResearchPassed,report.nativeOriginalRegressionPassed,checks=checks.Count,output}));
Environment.ExitCode=allPassed?0:1;

sealed class InlineProgress(Action<string> action):IProgress<string>{public void Report(string value)=>action(value);}
