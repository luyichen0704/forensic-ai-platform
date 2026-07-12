"""
Knowledge Base - Skill文件向量化知识库
将取证技能文件转化为向量化知识库，支持语义搜索和检索
"""
import os
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class SkillDocument:
    """技能文档"""
    skill_id: str
    name: str
    category: str
    content: str
    file_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None

@dataclass
class SearchResult:
    """搜索结果"""
    skill: SkillDocument
    score: float
    matched_sections: List[str]

class KnowledgeBase:
    """知识库管理器"""
    
    def __init__(self, skills_dir: str = None, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        初始化知识库
        
        Args:
            skills_dir: 技能文件目录
            embedding_model: 嵌入模型名称
        """
        self.skills_dir = skills_dir or self._find_skills_dir()
        self.embedding_model = embedding_model
        self.skills: Dict[str, SkillDocument] = {}
        self.embeddings_available = False
        
        # 尝试加载嵌入模型
        self._init_embedding_model()
        
        # 加载技能文件
        self._load_skills()
    
    def _find_skills_dir(self) -> str:
        """查找技能文件目录"""
        # 尝试多个可能的路径
        possible_paths = [
            Path(__file__).parent.parent.parent / "skills",
            Path.home() / "CompetitionTools" / "skills",
            Path("E:/CompetitionTools/skills"),
            Path("skills")
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_dir():
                return str(path)
        
        logger.warning("未找到技能文件目录")
        return ""
    
    def _init_embedding_model(self):
        """初始化嵌入模型"""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.embedding_model)
            self.embeddings_available = True
            logger.info(f"嵌入模型加载成功: {self.embedding_model}")
        except ImportError:
            logger.warning("sentence-transformers未安装，将使用简单的关键词匹配")
            self.model = None
        except Exception as e:
            logger.error(f"嵌入模型加载失败: {e}")
            self.model = None
    
    def _load_skills(self):
        """加载技能文件"""
        if not self.skills_dir or not os.path.exists(self.skills_dir):
            logger.warning(f"技能目录不存在: {self.skills_dir}")
            return
        
        skills_path = Path(self.skills_dir)
        
        # 遍历所有.md文件
        for md_file in skills_path.rglob("*.md"):
            try:
                # 跳过README和其他非技能文件
                if md_file.name.lower() in ["readme.md", "license.md", "changelog.md"]:
                    continue
                
                # 读取文件内容
                content = md_file.read_text(encoding='utf-8')
                
                # 提取技能信息
                skill_id = self._extract_skill_id(md_file)
                name = self._extract_skill_name(content, md_file)
                category = self._extract_skill_category(md_file)
                
                # 创建技能文档
                skill = SkillDocument(
                    skill_id=skill_id,
                    name=name,
                    category=category,
                    content=content,
                    file_path=str(md_file),
                    metadata={
                        "file_size": md_file.stat().st_size,
                        "last_modified": md_file.stat().st_mtime
                    }
                )
                
                # 生成嵌入向量
                if self.embeddings_available and self.model:
                    skill.embedding = self._generate_embedding(content)
                
                self.skills[skill_id] = skill
                logger.debug(f"加载技能: {skill_id} - {name}")
                
            except Exception as e:
                logger.error(f"加载技能文件失败 {md_file}: {e}")
        
        logger.info(f"成功加载 {len(self.skills)} 个技能文件")
    
    def _extract_skill_id(self, file_path: Path) -> str:
        """提取技能ID"""
        # 使用文件路径的相对路径作为ID
        relative_path = file_path.relative_to(self.skills_dir)
        return str(relative_path).replace('\\', '/').replace('.md', '')
    
    def _extract_skill_name(self, content: str, file_path: Path) -> str:
        """提取技能名称"""
        # 尝试从内容中提取标题
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        
        # 使用文件名
        return file_path.stem.replace('-', ' ').replace('_', ' ').title()
    
    def _extract_skill_category(self, file_path: Path) -> str:
        """提取技能类别"""
        # 从目录结构提取类别
        relative_path = file_path.relative_to(self.skills_dir)
        parts = relative_path.parts
        
        if len(parts) > 1:
            return parts[0]
        return "uncategorized"
    
    def _generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入向量"""
        if not self.model:
            return []
        
        try:
            # 截断文本以避免内存问题
            max_length = 1000
            if len(text) > max_length:
                text = text[:max_length]
            
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            return []
    
    def search(self, query: str, top_k: int = 5, 
               category_filter: str = None) -> List[SearchResult]:
        """
        搜索技能
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            category_filter: 类别过滤器
            
        Returns:
            搜索结果列表
        """
        if not self.skills:
            return []
        
        # 如果有嵌入模型，使用语义搜索
        if self.embeddings_available and self.model:
            return self._semantic_search(query, top_k, category_filter)
        else:
            return self._keyword_search(query, top_k, category_filter)
    
    def _semantic_search(self, query: str, top_k: int, 
                        category_filter: str = None) -> List[SearchResult]:
        """语义搜索"""
        # 生成查询嵌入
        query_embedding = self._generate_embedding(query)
        if not query_embedding:
            return self._keyword_search(query, top_k, category_filter)
        
        # 计算相似度
        results = []
        for skill in self.skills.values():
            if category_filter and skill.category != category_filter:
                continue
            
            if not skill.embedding:
                continue
            
            # 计算余弦相似度
            similarity = self._cosine_similarity(query_embedding, skill.embedding)
            
            # 找到匹配的段落
            matched_sections = self._find_matched_sections(query, skill.content)
            
            results.append(SearchResult(
                skill=skill,
                score=similarity,
                matched_sections=matched_sections
            ))
        
        # 按相似度排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:top_k]
    
    def _keyword_search(self, query: str, top_k: int, 
                       category_filter: str = None) -> List[SearchResult]:
        """关键词搜索"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        results = []
        for skill in self.skills.values():
            if category_filter and skill.category != category_filter:
                continue
            
            content_lower = skill.content.lower()
            
            # 计算关键词匹配分数
            score = 0.0
            
            # 完全匹配
            if query_lower in content_lower:
                score += 2.0
            
            # 单词匹配
            matched_words = 0
            for word in query_words:
                if word in content_lower:
                    matched_words += 1
            
            if query_words:
                score += matched_words / len(query_words)
            
            # 找到匹配的段落
            matched_sections = self._find_matched_sections(query, skill.content)
            
            if score > 0:
                results.append(SearchResult(
                    skill=skill,
                    score=score,
                    matched_sections=matched_sections
                ))
        
        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _find_matched_sections(self, query: str, content: str, 
                              context_lines: int = 3) -> List[str]:
        """找到匹配的段落"""
        query_lower = query.lower()
        lines = content.split('\n')
        
        matched_sections = []
        
        for i, line in enumerate(lines):
            if query_lower in line.lower():
                # 获取上下文
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                
                section = '\n'.join(lines[start:end])
                matched_sections.append(section)
        
        # 如果没有找到匹配，返回前几个段落
        if not matched_sections and lines:
            matched_sections.append('\n'.join(lines[:10]))
        
        return matched_sections[:3]  # 最多返回3个匹配段落
    
    def get_skill(self, skill_id: str) -> Optional[SkillDocument]:
        """获取指定技能"""
        return self.skills.get(skill_id)
    
    def get_skills_by_category(self, category: str) -> List[SkillDocument]:
        """按类别获取技能"""
        return [skill for skill in self.skills.values() 
                if skill.category == category]
    
    def get_all_categories(self) -> List[str]:
        """获取所有类别"""
        return list(set(skill.category for skill in self.skills.values()))
    
    def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        categories = {}
        for skill in self.skills.values():
            categories[skill.category] = categories.get(skill.category, 0) + 1
        
        return {
            "total_skills": len(self.skills),
            "categories": categories,
            "embeddings_available": self.embeddings_available,
            "skills_dir": self.skills_dir
        }
    
    def export_to_json(self, output_path: str):
        """导出知识库到JSON文件"""
        data = {
            "metadata": {
                "total_skills": len(self.skills),
                "embedding_model": self.embedding_model,
                "skills_dir": self.skills_dir
            },
            "skills": {}
        }
        
        for skill_id, skill in self.skills.items():
            data["skills"][skill_id] = {
                "name": skill.name,
                "category": skill.category,
                "file_path": skill.file_path,
                "content_preview": skill.content[:500] + "..." if len(skill.content) > 500 else skill.content,
                "metadata": skill.metadata
            }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"知识库已导出到: {output_path}")
    
    def rebuild_index(self):
        """重建索引"""
        self.skills.clear()
        self._load_skills()
        logger.info("知识库索引已重建")

# 测试代码
if __name__ == "__main__":
    # 测试知识库
    kb = KnowledgeBase()
    
    # 打印统计信息
    stats = kb.get_stats()
    print("知识库统计:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 测试搜索
    test_queries = [
        "如何分析E01磁盘镜像",
        "PCAP流量包分析",
        "APK逆向",
        "内存取证",
        "隐写术"
    ]
    
    for query in test_queries:
        print(f"\n搜索: {query}")
        results = kb.search(query, top_k=2)
        
        for i, result in enumerate(results):
            print(f"  {i+1}. {result.skill.name} (分数: {result.score:.2f})")
            print(f"     类别: {result.skill.category}")
            print(f"     文件: {result.skill.file_path}")
            if result.matched_sections:
                print(f"     匹配段落: {result.matched_sections[0][:100]}...")