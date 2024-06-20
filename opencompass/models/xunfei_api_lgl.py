import json
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Union

from opencompass.utils.prompt import PromptList
from langchain_community.chat_models import ChatSparkLLM
from langchain_core.messages import HumanMessage
from langchain_core.messages import AIMessage
import langchain
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


from opencompass.models.base_api import BaseAPIModel

PromptType = Union[PromptList, str]

import time

class XunFei_local(BaseAPIModel):
    """Model wrapper around XunFei.

    Args:
        path (str): Provided URL.
        appid (str): Provided APPID.
        api_secret (str): Provided APISecret.
        api_key (str): Provided APIKey.
        domain (str): Target version domain. Defaults to `general`.
        query_per_second (int): The maximum queries allowed per second
            between two consecutive calls of the API. Defaults to 2.
        max_seq_len (int): Unused here.
        meta_template (Dict, optional): The model's meta prompt
            template if needed, in case the requirement of injecting or
            wrapping of any meta instructions.
        retry (int): Number of retires if the API call fails. Defaults to 2.
    """

    def __init__(self,
                 path: str,
                 query_per_second: int = 2,
                 max_seq_len: int = 4096,
                 meta_template: Optional[Dict] = None,
                 retry: int = 2):
        super().__init__(path=path,
                         max_seq_len=max_seq_len,
                         query_per_second=query_per_second,
                         meta_template=meta_template,
                         retry=retry)

        from urllib.parse import urlencode, urlparse


    def generate(
        self,
        inputs: List[PromptType],
        max_out_len: int = 4096,
    ) -> List[str]:
        """Generate results given a list of inputs.

        Args:
            inputs (List[PromptType]): A list of strings or PromptDicts.
                The PromptDict should be organized in OpenCompass'
                API format.
            max_out_len (int): The maximum length of the output.

        Returns:
            List[str]: A list of generated strings.
        """
        '''
        with ThreadPoolExecutor() as executor:
            results = list(
                executor.map(self._generate, inputs,
                             [max_out_len] * len(inputs)))
        self.flush()
        return results
        '''
        results = []
        for input_i in inputs:
            result = self._generate(input_i, max_out_len)
            time.sleep(0.2)
            results.append(result)

        return results

    def _generate(
        self,
        input: PromptType,
        max_out_len: int = 4096,
    ) -> List[str]:
        """Generate results given an input.

        Args:
            inputs (PromptType): A string or PromptDict.
                The PromptDict should be organized in OpenCompass'
                API format.
            max_out_len (int): The maximum length of the output.

        Returns:
            str: The generated string.
        """

        chat = ChatSparkLLM(
            spark_app_id="<app_id>",
            spark_api_key="<api_key>",
            spark_api_secret="<api_secret>",
            spark_api_url=self.path,
            spark_llm_domain="generalv3.5",
            streaming=False,
            callbacks=[StreamingStdOutCallbackHandler()],
        )


        assert isinstance(input, (str, PromptList))

        # FIXME: messages only contains the last input
        if isinstance(input, str):
            # messages = [{'role': 'user', 'content': input}]
            messages = [HumanMessage(content=input,
                           temperature=0.0,
                           max_tokens=4096,
                           top_k=1.0,)]
        else:
            messages = []
            # word_ctr = 0
            # TODO: Implement truncation in PromptList
            for item in input:
                # msg = {'content': item['prompt']}

                # if word_ctr >= self.max_seq_len:
                #     break
                # if len(msg['content']) + word_ctr > self.max_seq_len:
                #     msg['content'] = msg['content'][word_ctr -
                #                                     self.max_seq_len:]
                # word_ctr += len(msg['content'])
                if item['role'] == 'HUMAN':
                    messages.append(HumanMessage(content=input,
                                             temperature=0.0,
                                             max_tokens=4096,
                                             top_k=1.0, ))
                elif item['role'] == 'BOT':
                    messages.append(AIMessage(content=input,
                                             temperature=0.0,
                                             max_tokens=4096,
                                             top_k=1.0, ))

            # in case the word break results in even number of messages
            # if len(messages) > 0 and len(messages) % 2 == 0:
            #     messages = messages[:-1]

        for _ in range(self.retry):
            self.acquire()
            ret = chat.invoke(messages).content.replace("<end>", "").replace('<ret><ret>', '\n').replace('<ret>', '')
            self.release()
            if isinstance(ret, str):
                return ret

        raise RuntimeError(ret)

if __name__ == '__main__':
    start = time.time()
    xunfei = XunFei_local(path="ws://10.80.16.101:9979/turing/v3/gpt")
    print(xunfei.generate(["There is a single choice question about high school european history. Answer the question by replying A, B, C or D.\nQuestion: This question refers to the following information.\nThe following excerpt is from a pamphlet.\nYou will do me the justice to remember, that I have always strenuously supported the Right of every man to his own opinion, however different that opinion might be to mine. He who denies to another this right, makes a slave of himself to his present opinion, because he precludes himself the right of changing it.\nThe most formidable weapon against errors of every kind is Reason. I have never used any other, and I trust I never shall.\nThe circumstance that has now taken place in France of the total abolition of the whole national order of priesthood, and of everything appertaining to compulsive systems of religion, and compulsive articles of faith, has not only precipitated my intention, but rendered a work of this kind exceedingly necessary, lest in the general wreck of superstition, of false systems of government, and false theology, we lose sight of morality, of humanity, and of the theology that is true.\nI believe in one God, and no more; and I hope for happiness beyond this life.\nI believe in the equality of man; and I believe that religious duties consist in doing justice, loving mercy, and endeavoring to make our fellow-creatures happy.\nI do not believe in the creed professed by the Jewish church, by the Roman church, by the Greek church, by the Turkish church, by the Protestant church, nor by any church that I know of. My own mind is my own church.\nAll national institutions of churches, whether Jewish, Christian or Turkish, appear to me no other than human inventions, set up to terrify and enslave mankind, and monopolize power and profit.\nI do not mean by this declaration to condemn those who believe otherwise; they have the same right to their belief as I have to mine.\n\u2014Thomas Paine, The Age of Reason, 1794\u20131795\nWhich of the following Enlightenment philosophes designed a system of checks and balances for government to avoid abuses of power?\nA. Jean Jacques Rousseau\nB. Baron Montesquieu\nC. Mary Wollstonecraft\nD. Adam Smith\nAnswer: \nB\n\nThere is a single choice question about high school european history. Answer the question by replying A, B, C or D.\nQuestion: This question refers to the following information.\nRead the following excerpt.\nThe revolutionary seed had penetrated into every country and spread more or less. It was greatly developed under the r\u00e9gime of the military despotism of Bonaparte. His conquests displaced a number of laws, institutions, and customs; broke through bonds sacred among all nations, strong enough to resist time itself; which is more than can be said of certain benefits conferred by these innovators.\nThe monarchs will fulfil the duties imposed upon them by Him who, by entrusting them with power, has charged them to watch over the maintenance of justice, and the rights of all, to avoid the paths of error, and tread firmly in the way of truth. Placed beyond the passions which agitate society, it is in days of trial chiefly that they are called upon to despoil realities of their false appearances, and to show themselves as they are, fathers invested with the authority belonging by right to the heads of families, to prove that, in days of mourning, they know how to be just, wise, and therefore strong, and that they will not abandon the people whom they ought to govern to be the sport of factions, to error and its consequences, which must involve the loss of society.\nUnion between the monarchs is the basis of the policy which must now be followed to save society from total ruin. . . .\nLet them not confound concessions made to parties with the good they ought to do for their people, in modifying, according to their recognized needs, such branches of the administration as require it.\nLet them be just, but strong; beneficent, but strict.\nLet them maintain religious principles in all their purity, and not allow the faith to be attacked and morality interpreted according to the social contract or the visions of foolish sectarians.\nLet them suppress Secret Societies; that gangrene of society.\n\u2014Klemens von Metternich, Political Confession of Faith, 1820\nWhich of the following was the greatest cause of the fears expressed by Metternich in the document above?\nA. The ideas of personal liberty and nationalism conceived during the Enlightenment resulted in radical revolutions that could spread throughout Europe.\nB. The conquest of Europe by Napoleon led to the creation of new factions and shifted the European balance of power.\nC. The power of monarchs had grown to the point where it needed to be checked by other powers within each nation or domination of civilians would occur.\nD. The rising and falling economic cycle of the newly emerging capitalist economy could lead to civilian unrest that must be suppressed.\nAnswer: \nA\n\nThere is a single choice question about high school european history. Answer the question by replying A, B, C or D.\nQuestion: This question refers to the following information.\nIn Russia there was nothing going on well, and [Souvarine] was in despair over the news he had received. His old companions were all turning to the politicians; the famous Nihilists who made Europe tremble-sons of village priests, of the lower middle class, of tradesmen-could not rise above the idea of national liberation, and seemed to believe that the world would be delivered-when they had killed their despot&\u2026\n\"Foolery! They'll never get out of it with their foolery.\"\nThen, lowering his voice still more, in a few bitter words he described his old dream of fraternity. He had renounced his rank and his fortune; he had gone among workmen, only in the hope of seeing at last the foundation of a new society of labour in common. All the sous in his pockets had long gone to the urchins of the settlement; he had been as tender as a brother with the colliers, smiling at their suspicion, winning them over by his quiet workmanlike ways and his dislike of chattering. But decidedly the fusion had not taken place.\nHis voice changed, his eyes grew bright, he fixed them on \u00e9tienne, directly addressing him:\n\"Now, do you understand that? These hatworkers at Marseilles who have won the great lottery prize of a hundred thousand francs have gone off at once and invested it, declaring that they are going to live without doing anything! Yes, that is your idea, all of you French workmen; you want to unearth a treasure in order to devour it alone afterwards in some lazy, selfish corner. You may cry out as much as you like against the rich, you haven't got courage enough to give back to the poor the money that luck brings you. You will never be worthy of happiness as long as you own anything, and your hatred of the bourgeois proceeds solely from an angry desire to be bourgeois yourselves in their place.\"\n\u00e9mile Zola, French writer, Germinal, 1885\nThe passage displays the direct concern for the welfare of the working classes that was typically a part of which movement?\nA. Capitalist\nB. Scientific\nC. Communist\nD. Existentialist\nAnswer: \nC\n\nThere is a single choice question about high school european history. Answer the question by replying A, B, C or D.\nQuestion: This question refers to the following information.\nThe excerpts below are from the Navigation Acts of 1651.\n[A]fter the first day of December, one thousand six hundred fifty and one, and from thence forwards, no goods or commodities whatsoever of the growth, production or manufacture of Asia, Africa or America, or of any part thereof; or of any islands belonging to them, or which are described or laid down in the usual maps or cards of those places, as well of the English plantations as others, shall be imported or brought into this Commonwealth of England, or into Ireland, or any other lands, islands, plantations, or territories to this Commonwealth belonging, or in their possession, in any other ship or ships, vessel or vessels whatsoever, but only in such as do truly and without fraud belong only to the people of this Commonwealth, or the plantations thereof, as the proprietors or right owners thereof; and whereof the master and mariners are also of the people of this Commonwealth, under the penalty of the forfeiture and loss of all the goods that shall be imported contrary to this act, , , ,\n[N]o goods or commodities of the growth, production, or manufacture of Europe, or of any part thereof, shall after the first day of December, one thousand six hundred fifty and one, be imported or brought into this Commonwealth of England, or any other lands or territories to this Commonwealth belonging, or in their possession, in any ship or ships, vessel or vessels whatsoever, but in such as do truly and without fraud belong only to the people of this Commonwealth, and in no other, except only such foreign ships and vessels as do truly and properly belong to the people of that country or place, of which the said goods are the growth, production or manufacture.\nWhich of the following best describes the outcome of the Navigation Acts of 1651?\nA. They served as a catalyst for the growth of English shipping and overseas trade, but did little to limit the prospects of the Dutch in the seventeenth century.\nB. They brought about almost immediate hardships for the Dutch economy as their dominance of overseas trade quickly ended.\nC. They were rescinded during the restoration of the Stuarts as they sought normal diplomatic relations with the Dutch so not as to need Parliament's financial support for war.\nD. They led to nearly a century of recurrent war between England and the Netherlands, which would not end until after American independence.\nAnswer: \nA\n\nThere is a single choice question about high school european history. Answer the question by replying A, B, C or D.\nQuestion: This question refers to the following information.\nAlbeit the king's Majesty justly and rightfully is and ought to be the supreme head of the Church of England, and so is recognized by the clergy of this realm in their convocations, yet nevertheless, for corroboration and confirmation thereof, and for increase of virtue in Christ's religion within this realm of England, and to repress and extirpate all errors, heresies, and other enormities and abuses heretofore used in the same, be it enacted, by authority of this present Parliament, that the king, our sovereign lord, his heirs and successors, kings of this realm, shall be taken, accepted, and reputed the only supreme head in earth of the Church of England, called Anglicans Ecclesia; and shall have and enjoy, annexed and united to the imperial crown of this realm, as well the title and style thereof, as all honors, dignities, preeminences, jurisdictions, privileges, authorities, immunities, profits, and commodities to the said dignity of the supreme head of the same Church belonging and appertaining; and that our said sovereign lord, his heirs and successors, kings of this realm, shall have full power and authority from time to time to visit, repress, redress, record, order, correct, restrain, and amend all such errors, heresies, abuses, offenses, contempts, and enormities, whatsoever they be, which by any manner of spiritual authority or jurisdiction ought or may lawfully be reformed, repressed, ordered, redressed, corrected, restrained, or amended, most to the pleasure of Almighty God, the increase of virtue in Christ's religion, and for the conservation of the peace, unity, and tranquility of this realm; any usage, foreign land, foreign authority, prescription, or any other thing or things to the contrary hereof notwithstanding.\nEnglish Parliament, Act of Supremacy, 1534\nFrom the passage, one may infer that the English Parliament wished to argue that the Act of Supremacy would\nA. give the English king a new position of authority\nB. give the position of head of the Church of England to Henry VIII alone and exclude his heirs\nC. establish Calvinism as the one true theology in England\nD. end various forms of corruption plaguing the Church in England\nAnswer: \nD\n\nThere is a single choice question about high school european history. Answer the question by replying A, B, C or D.\nQuestion: This question refers to the following information.\nIn order to make the title of this discourse generally intelligible, I have translated the term \"Protoplasm,\" which is the scientific name of the substance of which I am about to speak, by the words \"the physical basis of life.\" I suppose that, to many, the idea that there is such a thing as a physical basis, or matter, of life may be novel\u2014so widely spread is the conception of life as something which works through matter. \u2026 Thus the matter of life, so far as we know it (and we have no right to speculate on any other), breaks up, in consequence of that continual death which is the condition of its manifesting vitality, into carbonic acid, water, and nitrogenous compounds, which certainly possess no properties but those of ordinary matter.\nThomas Henry Huxley, \"The Physical Basis of Life,\" 1868\nFrom the passage, one may infer that Huxley argued that \"life\" was\nA. a force that works through matter\nB. essentially a philosophical notion\nC. merely a property of a certain kind of matter\nD. a supernatural phenomenon\nAnswer: "]))
    end = time.time()
    print('Xunfei local time cost ', end - start)


