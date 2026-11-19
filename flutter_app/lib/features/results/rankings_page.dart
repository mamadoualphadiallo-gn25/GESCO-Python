import 'package:flutter/material.dart';
import '../../data/local/app_database.dart';
import '../../app/theme/app_theme.dart';
class RankingsPage extends StatefulWidget {
 const RankingsPage({super.key,required this.database});
 final AppDatabase database;
 @override State<RankingsPage> createState()=>_RankingsPageState();
}
class _RankingsPageState extends State<RankingsPage>{
 List<Map<String,Object?>> classes=[],periods=[],results=[];
 int? classId,periodId; bool loading=false;
 @override void initState(){super.initState();_init();}
 Future<void> _init() async {
  try{
   final c=await widget.database.customSelect('SELECT id,name FROM classes ORDER BY name').get();
   final p=await widget.database.customSelect('SELECT id,label,code,school_year_id FROM periods ORDER BY sequence').get();
   if(!mounted)return;
   setState(()=>{classes=c.map((e)=>Map<String,Object?>.from(e.data)).toList(),periods=p.map((e)=>Map<String,Object?>.from(e.data)).toList()});
  }catch(e){_notify('Erreur de chargement : $e');}
 }
 Future<void> _calculate() async {
  if(classId==null||periodId==null)return; setState(()=>loading=true);
  try{
   final rows=await widget.database.customSelect('''
    SELECT st.id AS student_id,st.matricule,st.last_name,st.first_name,
    SUM(g.score*g.coefficient_snapshot)/NULLIF(SUM(g.coefficient_snapshot),0) AS average
    FROM enrollments en JOIN students st ON st.id=en.student_id
    LEFT JOIN grades g ON g.student_id=st.id AND g.period_id=? AND g.assessment_type='period' AND g.score IS NOT NULL
    WHERE en.class_id=? AND st.is_archived=0
    GROUP BY st.id,st.matricule,st.last_name,st.first_name
    ORDER BY average DESC,st.last_name COLLATE NOCASE,st.first_name COLLATE NOCASE
   ''',variables:[Variable.withInt(periodId!),Variable.withInt(classId!)]).get();
   final mapped=rows.map((e)=>Map<String,Object?>.from(e.data)).toList();
   var rank=0; double? previous;
   for(var i=0;i<mapped.length;i++){
    final avg=(mapped[i]['average'] as num?)?.toDouble();
    if(avg==null){mapped[i]['rank']=null;continue;}
    if(previous==null||(previous-avg).abs()>0.000001)rank=i+1;
    mapped[i]['rank']=rank;previous=avg;
   }
   if(mounted)setState(()=>results=mapped);
  }catch(e){_notify('Calcul impossible : $e');}
  if(mounted)setState(()=>loading=false);
 }
 void _notify(String s){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(s)));}
 String _fmt(Object? v)=>v==null?'—':(v as num).toStringAsFixed(2);
 @override Widget build(BuildContext context){
  final avgs=results.map((r)=>(r['average'] as num?)?.toDouble()).whereType<double>().toList();
  final passed=avgs.where((v)=>v>=10).length;
  final mean=avgs.isEmpty?null:avgs.reduce((a,b)=>a+b)/avgs.length;
  final best=avgs.isEmpty?null:avgs.reduce((a,b)=>a>b?a:b);
  final worst=avgs.isEmpty?null:avgs.reduce((a,b)=>a<b?a:b);
  return Padding(padding:const EdgeInsets.all(26),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
   const Text('Classements et statistiques',style:TextStyle(fontSize:28,fontWeight:FontWeight.w800,color:AppTheme.ink)),
   const SizedBox(height:6),const Text('Les notes non saisies ne sont pas considérées comme zéro.',style:TextStyle(color:AppTheme.muted)),
   const SizedBox(height:18),Wrap(spacing:12,runSpacing:12,children:[
    SizedBox(width:250,child:DropdownButtonFormField<int>(value:classId,decoration:const InputDecoration(labelText:'Classe'),items:classes.map((e)=>DropdownMenuItem(value:e['id'] as int,child:Text(e['name'].toString()))).toList(),onChanged:(v)=>setState(()=>classId=v))),
    SizedBox(width:250,child:DropdownButtonFormField<int>(value:periodId,decoration:const InputDecoration(labelText:'Période'),items:periods.map((e)=>DropdownMenuItem(value:e['id'] as int,child:Text(e['label'].toString()))).toList(),onChanged:(v)=>setState(()=>periodId=v))),
    FilledButton.icon(onPressed:classId!=null&&periodId!=null&&!loading?_calculate:null,icon:const Icon(Icons.calculate_outlined),label:const Text('Calculer')),
   ]),
   const SizedBox(height:16),
   if(results.isNotEmpty)Wrap(spacing:10,runSpacing:10,children:[
    _Stat('Effectif', '${results.length}'),_Stat('Moyenne classe',_fmt(mean)),_Stat('Meilleure',_fmt(best)),_Stat('Plus faible',_fmt(worst)),_Stat('Admis ≥ 10','$passed'),_Stat('Réussite',avgs.isEmpty?'—':'${(passed*100/avgs.length).toStringAsFixed(1)} %'),
   ]),
   const SizedBox(height:14),Expanded(child:Card(child:loading?const Center(child:CircularProgressIndicator()):results.isEmpty?const Center(child:Text('Sélectionnez une classe et une période.')):SingleChildScrollView(child:DataTable(columns:const [DataColumn(label:Text('Rang')),DataColumn(label:Text('Matricule')),DataColumn(label:Text('Nom et prénom')),DataColumn(label:Text('Moyenne /20'))],rows:results.map((r)=>DataRow(cells:[DataCell(Text(r['rank']?.toString()??'—')),DataCell(Text(r['matricule'].toString())),DataCell(Text('${r['last_name']} ${r['first_name']}')),DataCell(Text(_fmt(r['average'])))] )).toList())))),
  ]));
 }
}
class _Stat extends StatelessWidget{
 const _Stat(this.label,this.value);final String label,value;
 @override Widget build(BuildContext context)=>Container(width:155,padding:const EdgeInsets.all(13),decoration:BoxDecoration(color:Colors.white,borderRadius:BorderRadius.circular(12),border:Border.all(color:AppTheme.border)),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(label,style:const TextStyle(fontSize:11,color:AppTheme.muted)),const SizedBox(height:6),Text(value,style:const TextStyle(fontSize:18,fontWeight:FontWeight.w800,color:AppTheme.ink))]));
}
