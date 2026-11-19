import 'package:flutter/material.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import '../../data/local/app_database.dart';
import '../../app/theme/app_theme.dart';

class BulletinsPage extends StatefulWidget {
 const BulletinsPage({super.key,required this.database});
 final AppDatabase database;
 @override State<BulletinsPage> createState()=>_BulletinsPageState();
}
class _BulletinsPageState extends State<BulletinsPage>{
 List<Map<String,Object?>> classes=[],periods=[],students=[];
 int? classId,periodId,studentId; bool loading=false,printing=false;
 @override void initState(){super.initState();_loadClasses();}
 Future<void> _loadClasses() async{
  try{final rows=await widget.database.customSelect('SELECT id,name FROM classes ORDER BY name').get();if(!mounted)return;setState(()=>classes=rows.map((e)=>Map<String,Object?>.from(e.data)).toList());}catch(e){_msg('Chargement impossible : $e');}
 }
 Future<void> _loadPeriods() async{
  if(classId==null)return;
  try{final rows=await widget.database.customSelect('SELECT DISTINCT p.id,p.label,p.code,p.sequence FROM periods p JOIN classes c ON c.school_year_id=p.school_year_id WHERE c.id=? ORDER BY p.sequence',variables:[Variable.withInt(classId!)]).get();if(!mounted)return;setState(()=>{periods=rows.map((e)=>Map<String,Object?>.from(e.data)).toList(),periodId=null});}catch(e){_msg('Périodes indisponibles : $e');}
 }
 Future<void> _loadStudents() async{
  if(classId==null)return;setState(()=>loading=true);
  try{final rows=await widget.database.customSelect('SELECT st.id,st.matricule,st.last_name,st.first_name,st.sex FROM enrollments en JOIN students st ON st.id=en.student_id WHERE en.class_id=? AND st.is_archived=0 ORDER BY st.last_name,st.first_name',variables:[Variable.withInt(classId!)]).get();if(!mounted)return;setState(()=>{students=rows.map((e)=>Map<String,Object?>.from(e.data)).toList(),studentId=null});}catch(e){_msg('Élèves indisponibles : $e');}
  if(mounted)setState(()=>loading=false);
 }
 Future<void> _printBulletin() async{
  if(studentId==null||periodId==null||classId==null)return;setState(()=>printing=true);
  try{
   final s=students.firstWhere((e)=>e['id']==studentId),cl=classes.firstWhere((e)=>e['id']==classId),per=periods.firstWhere((e)=>e['id']==periodId);
   final rows=await widget.database.customSelect('SELECT su.name AS subject_name,g.score,g.max_score,g.coefficient_snapshot FROM grades g JOIN subjects su ON su.id=g.subject_id JOIN class_subjects cs ON cs.class_id=? AND cs.subject_id=g.subject_id WHERE g.student_id=? AND g.period_id=? AND g.assessment_type=? AND g.score IS NOT NULL ORDER BY su.name',variables:[Variable.withInt(classId!),Variable.withInt(studentId!),Variable.withInt(periodId!),Variable.withString('period')]).get();
   double weighted=0,coeffTotal=0;final data=<List<String>>[];
   for(final row in rows){final score=(row.data['score'] as num).toDouble(),max=(row.data['max_score'] as num).toDouble(),coef=(row.data['coefficient_snapshot'] as num).toDouble();final normalized=max==0?0:score*20/max;weighted+=normalized*coef;coeffTotal+=coef;data.add([row.data['subject_name'].toString(),normalized.toStringAsFixed(2),coef.toStringAsFixed(2),(normalized*coef).toStringAsFixed(2)]);}
   final average=coeffTotal==0?null:weighted/coeffTotal;final doc=pw.Document();
   doc.addPage(pw.MultiPage(pageFormat:PdfPageFormat.a4,margin:const pw.EdgeInsets.all(32),build:(context)=>[
    pw.Center(child:pw.Text('BULLETIN DE NOTES',style:pw.TextStyle(fontSize:20,fontWeight:pw.FontWeight.bold))),
    pw.Center(child:pw.Text(per['label'].toString())),pw.SizedBox(height:18),
    pw.Text('Établissement : __________________________________________'),pw.Text('Année scolaire : _________________________________________'),
    pw.SizedBox(height:12),pw.Text('Élève : ${s['last_name']} ${s['first_name']}',style:pw.TextStyle(fontWeight:pw.FontWeight.bold,fontSize:12)),
    pw.Text('Matricule : ${s['matricule']}    Classe : ${cl['name']}'),pw.Text('Sexe : ${s['sex']??'—'}    Effectif : ${students.length}'),pw.SizedBox(height:18),
    pw.TableHelper.fromTextArray(headers:['Matière','Note /20','Coef.','Note pondérée'],data:data,headerStyle:pw.TextStyle(fontWeight:pw.FontWeight.bold,fontSize:9),cellStyle:const pw.TextStyle(fontSize:9),cellHeight:25,border:pw.TableBorder.all(color:PdfColors.grey600,width:.5)),
    pw.SizedBox(height:16),pw.Text('Total coefficients : ${coeffTotal.toStringAsFixed(2)}'),pw.Text('Total notes pondérées : ${weighted.toStringAsFixed(2)}'),
    pw.Text('Moyenne générale : ${average?.toStringAsFixed(2)??'Non calculable'} / 20',style:pw.TextStyle(fontSize:14,fontWeight:pw.FontWeight.bold)),
    pw.SizedBox(height:22),pw.Text('Appréciation générale : __________________________________________________________'),pw.SizedBox(height:35),
    pw.Row(mainAxisAlignment:pw.MainAxisAlignment.spaceBetween,children:[pw.Text('Signature du professeur'),pw.Text('Signature du directeur')]),pw.SizedBox(height:30),pw.Center(child:pw.Text('Cachet de l’établissement')),
   ]));
   await Printing.layoutPdf(onLayout:(format)=>doc.save(),name:'Bulletin_${s['matricule']}_${per['code']}.pdf');
  }catch(e){_msg('Génération du bulletin impossible : $e');}
  if(mounted)setState(()=>printing=false);
 }
 void _msg(String v){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(v)));}
 @override Widget build(BuildContext context)=>Padding(padding:const EdgeInsets.all(26),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
  const Text('Bulletins scolaires',style:TextStyle(fontSize:28,fontWeight:FontWeight.w800,color:AppTheme.ink)),const SizedBox(height:6),const Text('Générer et imprimer un bulletin individuel à partir des notes enregistrées.',style:TextStyle(color:AppTheme.muted)),const SizedBox(height:20),
  Wrap(spacing:12,runSpacing:12,children:[
   SizedBox(width:230,child:DropdownButtonFormField<int>(value:classId,decoration:const InputDecoration(labelText:'Classe'),items:classes.map((e)=>DropdownMenuItem(value:e['id'] as int,child:Text(e['name'].toString()))).toList(),onChanged:(v){setState(()=>{classId=v,periods=[],periodId=null,students=[],studentId=null});_loadPeriods();_loadStudents();})),
   SizedBox(width:230,child:DropdownButtonFormField<int>(value:periodId,decoration:const InputDecoration(labelText:'Période'),items:periods.map((e)=>DropdownMenuItem(value:e['id'] as int,child:Text(e['label'].toString()))).toList(),onChanged:(v)=>setState(()=>periodId=v))),
   SizedBox(width:260,child:DropdownButtonFormField<int>(value:studentId,decoration:const InputDecoration(labelText:'Élève'),items:students.map((e)=>DropdownMenuItem(value:e['id'] as int,child:Text('${e['last_name']} ${e['first_name']}'))).toList(),onChanged:(v)=>setState(()=>studentId=v))),
   FilledButton.icon(onPressed:studentId!=null&&periodId!=null&&!printing?_printBulletin:null,icon:const Icon(Icons.picture_as_pdf_outlined),label:Text(printing?'Préparation…':'Aperçu / Imprimer')),
  ]),
  const SizedBox(height:18),Expanded(child:Card(child:loading?const Center(child:CircularProgressIndicator()):students.isEmpty?const Center(child:Text('Sélectionnez une classe pour afficher les élèves.')):ListView.separated(itemCount:students.length,separatorBuilder:(_,__)=>const Divider(height:1),itemBuilder:(context,i)=>ListTile(selected:students[i]['id']==studentId,onTap:()=>setState(()=>studentId=students[i]['id'] as int),leading:const Icon(Icons.person_outline),title:Text('${students[i]['last_name']} ${students[i]['first_name']}'),subtitle:Text('Matricule : ${students[i]['matricule']}'))))),
 ]));
}
