import 'package:flutter/material.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import '../../data/local/app_database.dart';
import '../../app/theme/app_theme.dart';

class TeacherSheetPage extends StatefulWidget {
 const TeacherSheetPage({super.key,required this.database});
 final AppDatabase database;
 @override State<TeacherSheetPage> createState()=>_TeacherSheetPageState();
}
class _TeacherSheetPageState extends State<TeacherSheetPage>{
 List<Map<String,Object?>> classes=[],subjects=[],students=[];
 int? classId,subjectId; bool loading=false;
 @override void initState(){super.initState();_loadOptions();}
 Future<void> _loadOptions() async{
  try{
   final c=await widget.database.customSelect('SELECT id,name FROM classes ORDER BY name').get();
   if(!mounted)return;setState(()=>classes=c.map((e)=>Map<String,Object?>.from(e.data)).toList());
  }catch(e){_msg('Erreur : $e');}
 }
 Future<void> _loadSubjects() async{
  if(classId==null)return;
  final s=await widget.database.customSelect('SELECT su.id,su.name,cs.coefficient FROM class_subjects cs JOIN subjects su ON su.id=cs.subject_id WHERE cs.class_id=? ORDER BY su.name',variables:[Variable.withInt(classId!)]).get();
  if(!mounted)return;setState(()=>subjects=s.map((e)=>Map<String,Object?>.from(e.data)).toList());
 }
 Future<void> _loadStudents() async{
  if(classId==null)return;setState(()=>loading=true);
  try{
   final rows=await widget.database.customSelect('SELECT st.matricule,st.last_name,st.first_name FROM enrollments en JOIN students st ON st.id=en.student_id WHERE en.class_id=? AND st.is_archived=0 ORDER BY st.last_name,st.first_name',variables:[Variable.withInt(classId!)]).get();
   if(!mounted)return;setState(()=>students=rows.map((e)=>Map<String,Object?>.from(e.data)).toList());
  }catch(e){_msg('Impossible de charger les élèves : $e');}
  if(mounted)setState(()=>loading=false);
 }
 Future<void> _printSheet() async{
  final subject=subjects.where((s)=>s['id']==subjectId).firstOrNull;
  if(subject==null||students.isEmpty){_msg('Sélectionne une classe, une matière et charge la liste.');return;}
  final className=classes.where((c)=>c['id']==classId).firstOrNull?['name']?.toString()??'Classe';
  final doc=pw.Document();
  doc.addPage(pw.MultiPage(pageFormat:PdfPageFormat.a4,margin:const pw.EdgeInsets.all(28),build:(context)=>[
   pw.Center(child:pw.Text('FICHE DE SAISIE DES NOTES',style:pw.TextStyle(fontSize:18,fontWeight:pw.FontWeight.bold))),
   pw.SizedBox(height:8),
   pw.Text('Classe : $className'),
   pw.Text('Matière : ${subject['name']}    Coefficient : ${subject['coefficient']}'),
   pw.Text('Année scolaire : ____________________    Période : ____________________'),
   pw.SizedBox(height:16),
   pw.TableHelper.fromTextArray(
    headers:['N°','Matricule','Nom et prénom','Note /20','Observation'],
    data:List.generate(students.length,(i)=>[
     '${i+1}',students[i]['matricule'].toString(),
     '${students[i]['last_name']} ${students[i]['first_name']}','',''
    ]),
    headerStyle:pw.TextStyle(fontWeight:pw.FontWeight.bold,fontSize:9),
    cellStyle:const pw.TextStyle(fontSize:8),
    cellHeight:27,
    border:pw.TableBorder.all(color:PdfColors.grey600,width:.5),
    columnWidths:{0:const pw.FixedColumnWidth(28),1:const pw.FixedColumnWidth(85),2:const pw.FlexColumnWidth(2),3:const pw.FixedColumnWidth(65),4:const pw.FlexColumnWidth(1.4)},
   ),
   pw.SizedBox(height:20),
   pw.Row(mainAxisAlignment:pw.MainAxisAlignment.spaceBetween,children:[pw.Text('Signature du professeur : ____________________'),pw.Text('Date : ______________')]),
  ]));
  await Printing.layoutPdf(onLayout:(format)=>doc.save(),name:'GESCO_Fiche_${className}_${subject['name']}.pdf');
 }
 void _msg(String s){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(s)));}
 @override Widget build(BuildContext context)=>Padding(padding:const EdgeInsets.all(26),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
  const Text('Fiches de notes pour les professeurs',style:TextStyle(fontSize:28,fontWeight:FontWeight.w800,color:AppTheme.ink)),
  const SizedBox(height:6),const Text('Imprimer une liste nominative par classe et par matière pour la saisie manuscrite.',style:TextStyle(color:AppTheme.muted)),
  const SizedBox(height:20),Wrap(spacing:12,runSpacing:12,children:[
   SizedBox(width:260,child:DropdownButtonFormField<int>(value:classId,decoration:const InputDecoration(labelText:'Classe'),items:classes.map((e)=>DropdownMenuItem(value:e['id'] as int,child:Text(e['name'].toString()))).toList(),onChanged:(v){setState(()=>{classId=v,subjectId=null,subjects=[],students=[]});_loadSubjects();})),
   SizedBox(width:260,child:DropdownButtonFormField<int>(value:subjectId,decoration:const InputDecoration(labelText:'Matière'),items:subjects.map((e)=>DropdownMenuItem(value:e['id'] as int,child:Text(e['name'].toString()))).toList(),onChanged:(v)=>setState(()=>subjectId=v))),
   FilledButton.icon(onPressed:classId==null||loading?null:_loadStudents,icon:const Icon(Icons.people_outline),label:const Text('Afficher les élèves')),
   FilledButton.icon(onPressed:students.isEmpty?null:_printSheet,icon:const Icon(Icons.print_outlined),label:const Text('Imprimer la fiche PDF')),
  ]),
  const SizedBox(height:18),Expanded(child:Card(child:loading?const Center(child:CircularProgressIndicator()):students.isEmpty?const Center(child:Text('Choisis une classe puis affiche les élèves.')):ListView.separated(itemCount:students.length,separatorBuilder:(_,__)=>const Divider(height:1),itemBuilder:(context,i)=>ListTile(leading:Text('${i+1}'.padLeft(2,'0')),title:Text('${students[i]['last_name']} ${students[i]['first_name']}'),subtitle:Text('Matricule : ${students[i]['matricule']}'))))),
 ]));
}
