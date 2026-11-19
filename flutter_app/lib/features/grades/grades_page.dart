import 'package:flutter/material.dart';
import '../../data/local/app_database.dart';
import '../../app/theme/app_theme.dart';

class GradesPage extends StatefulWidget {
  const GradesPage({super.key, required this.database});
  final AppDatabase database;
  @override
  State<GradesPage> createState() => _GradesPageState();
}

class _GradesPageState extends State<GradesPage> {
  List<Map<String,Object?>> classes=[];
  List<Map<String,Object?>> periods=[];
  List<Map<String,Object?>> students=[];
  List<Map<String,Object?>> subjects=[];
  int? classId, periodId;
  bool loading=false, saving=false;
  final Map<String,TextEditingController> controllers={};

  @override
  void initState(){super.initState();_init();}
  @override
  void dispose(){for(final c in controllers.values){c.dispose();}super.dispose();}

  Future<void> _init() async {
    try {
      final c=await widget.database.customSelect('SELECT id,name FROM classes ORDER BY name').get();
      final p=await widget.database.customSelect('SELECT id,label,code,school_year_id FROM periods ORDER BY sequence').get();
      if(!mounted)return;
      setState((){
        classes=c.map((e)=>Map<String,Object?>.from(e.data)).toList();
        periods=p.map((e)=>Map<String,Object?>.from(e.data)).toList();
      });
    } catch(e){_message('Impossible de charger les classes et périodes : $e');}
  }

  Future<void> _loadGrid() async {
    if(classId==null||periodId==null)return;
    setState(()=>loading=true);
    try {
      final s=await widget.database.customSelect('''
        SELECT st.id, st.matricule, st.last_name, st.first_name
        FROM enrollments en JOIN students st ON st.id=en.student_id
        WHERE en.class_id=? AND st.is_archived=0 ORDER BY st.last_name,st.first_name
      ''',variables:[Variable.withInt(classId!)]).get();
      final m=await widget.database.customSelect('''
        SELECT cs.subject_id, su.name, cs.coefficient
        FROM class_subjects cs JOIN subjects su ON su.id=cs.subject_id
        WHERE cs.class_id=? ORDER BY su.name
      ''',variables:[Variable.withInt(classId!)]).get();
      final existing=await widget.database.customSelect('''
        SELECT student_id,subject_id,score FROM grades
        WHERE period_id=? AND assessment_type='period'
      ''',variables:[Variable.withInt(periodId!)]).get();
      for(final c in controllers.values){c.dispose();}
      controllers.clear();
      for(final student in s){
        for(final subject in m){
          final key='${student.data['id']}_${subject.data['subject_id']}';
          final match=existing.where((g)=>g.data['student_id']==student.data['id']&&g.data['subject_id']==subject.data['subject_id']).toList();
          controllers[key]=TextEditingController(text:match.isEmpty||match.first.data['score']==null?'':match.first.data['score'].toString());
        }
      }
      if(!mounted)return;
      setState((){
        students=s.map((e)=>Map<String,Object?>.from(e.data)).toList();
        subjects=m.map((e)=>Map<String,Object?>.from(e.data)).toList();
        loading=false;
      });
    } catch(e){if(mounted)setState(()=>loading=false);_message('Erreur de chargement : $e');}
  }

  Future<void> _save() async {
    setState(()=>saving=true);
    try {
      await widget.database.transaction(() async {
        for(final student in students){
          for(final subject in subjects){
            final sid=student['id'] as int, subid=subject['subject_id'] as int;
            final key='${sid}_$subid';
            final raw=controllers[key]?.text.trim()??'';
            if(raw.isEmpty) {
              await widget.database.customStatement("DELETE FROM grades WHERE student_id=? AND subject_id=? AND period_id=? AND assessment_type='period'",[sid,subid,periodId]);
              continue;
            }
            final score=double.tryParse(raw.replaceAll(',','.'));
            if(score==null||score<0||score>20) throw FormatException('Note invalide pour ${student['last_name']} / ${subject['name']} : saisir une note entre 0 et 20.');
            await widget.database.customStatement("DELETE FROM grades WHERE student_id=? AND subject_id=? AND period_id=? AND assessment_type='period'",[sid,subid,periodId]);
            await widget.database.customStatement('''
              INSERT INTO grades(student_id,subject_id,period_id,assessment_type,score,max_score,coefficient_snapshot)
              VALUES(?,?,?,'period',?,20,?)
            ''',[sid,subid,periodId,score,subject['coefficient']]);
          }
        }
      });
      _message('Notes enregistrées dans la base locale.');
    } catch(e){_message('Enregistrement interrompu : $e');}
    if(mounted)setState(()=>saving=false);
  }

  void _message(String message){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(message)));}
  @override
  Widget build(BuildContext context)=>Padding(
    padding:const EdgeInsets.all(26),
    child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
      const Text('Saisie des notes',style:TextStyle(fontSize:28,fontWeight:FontWeight.w800,color:AppTheme.ink)),
      const SizedBox(height:6),
      const Text('Notes sur 20, enregistrées localement par élève, matière et période.',style:TextStyle(color:AppTheme.muted)),
      const SizedBox(height:20),
      Wrap(spacing:12,runSpacing:12,children:[
        SizedBox(width:260,child:DropdownButtonFormField<int>(
          value:classId,decoration:const InputDecoration(labelText:'Classe'),
          items:classes.map((e)=>DropdownMenuItem(value:e['id'] as int,child:Text(e['name'].toString()))).toList(),
          onChanged:(v)=>setState(()=>classId=v))),
        SizedBox(width:260,child:DropdownButtonFormField<int>(
          value:periodId,decoration:const InputDecoration(labelText:'Période'),
          items:periods.map((e)=>DropdownMenuItem(value:e['id'] as int,child:Text(e['label'].toString()))).toList(),
          onChanged:(v)=>setState(()=>periodId=v))),
        FilledButton.icon(onPressed:classId!=null&&periodId!=null?_loadGrid:null,icon:const Icon(Icons.search),label:const Text('Afficher')),
        FilledButton.icon(onPressed:students.isNotEmpty&&!saving?_save:null,icon:const Icon(Icons.save_outlined),label:Text(saving?'Enregistrement…':'Enregistrer les notes')),
      ]),
      const SizedBox(height:18),
      Expanded(child:Card(child:loading?const Center(child:CircularProgressIndicator()):
        students.isEmpty?const Center(child:Text('Choisissez une classe et une période, puis cliquez sur Afficher.')):
        subjects.isEmpty?const Center(child:Text('Aucune matière affectée à cette classe. Configurez ses matières avant la saisie.')):
        Scrollbar(child:SingleChildScrollView(child:SingleChildScrollView(scrollDirection:Axis.horizontal,child:DataTable(
          columns:[
            const DataColumn(label:Text('Matricule')),
            const DataColumn(label:Text('Élève')),
            ...subjects.map((s)=>DataColumn(label:Column(mainAxisAlignment:MainAxisAlignment.center,crossAxisAlignment:CrossAxisAlignment.start,children:[
              Text(s['name'].toString()),Text('Coef. ${s['coefficient']}',style:const TextStyle(fontSize:11,color:AppTheme.muted))
            ]))),
          ],
          rows:students.map((st)=>DataRow(cells:[
            DataCell(Text(st['matricule'].toString())),
            DataCell(Text('${st['last_name']} ${st['first_name']}')),
            ...subjects.map((su){
              final ctl=controllers['${st['id']}_${su['subject_id']}']!;
              return DataCell(SizedBox(width:76,child:TextField(controller:ctl,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(hintText:'—',contentPadding:EdgeInsets.symmetric(horizontal:8,vertical:8)),)));
            }),
          ])).toList(),
        ))))),
      )),
    ]),
  );
}
