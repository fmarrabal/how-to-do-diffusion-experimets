using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Security.Cryptography;
using DiffAtOnce.Academy.Tutor;

var folder = Path.GetFullPath(args[0]);
var report = Path.GetFullPath(args[1]);
if (File.Exists(report)) throw new IOException("Refuse to overwrite completed parity evidence.");
var type=typeof(TutorService);
var serializer=type.GetMethod("TrainingCompatibleJson",BindingFlags.NonPublic|BindingFlags.Static)!;
var system=(string)type.GetField("GroundedInstructions",BindingFlags.NonPublic|BindingFlags.Static)!.GetValue(null)!;
var checks=new List<object>(); var passed=true;
foreach(var path in Directory.EnumerateFiles(folder,"input-*.json").Order())
{
    using var input=JsonDocument.Parse(await File.ReadAllTextAsync(path));
    var user=(string)serializer.Invoke(null,new object[]{input.RootElement})!;
    var actual=Encoding.UTF8.GetBytes(TutorService.ChatPrompt(system,user));
    var expected=await File.ReadAllBytesAsync(path.Replace("input-","expected-").Replace(".json",".txt"));
    var same=actual.SequenceEqual(expected);passed&=same;
    checks.Add(new { id=Path.GetFileName(path),passed=same,actual_bytes=actual.Length,expected_bytes=expected.Length,actual_sha256=Convert.ToHexString(SHA256.HashData(actual)).ToLowerInvariant(),expected_sha256=Convert.ToHexString(SHA256.HashData(expected)).ToLowerInvariant()});
}
await File.WriteAllTextAsync(report,JsonSerializer.Serialize(new{passed,total=checks.Count,checks,scope="Byte-for-byte Python tokenizer chat template versus C# training-profile serialization. No inference, held-out reevaluation or weight changes."},new JsonSerializerOptions{WriteIndented=true}));
Console.WriteLine($"Prompt bytes parity: {checks.Count} cases, {(passed?"PASS":"FAIL")}");
return passed?0:1;
